from __future__ import annotations

from datetime import datetime as dt
import asyncio

import asyncpg
import discord
from discord.ext import commands, vbu

from cogs import utils
from cogs.utils import types


class Marriage(vbu.Cog[types.Bot]):

    async def get_max_partners_for_member(
            self,
            user: discord.Member) -> int:
        """
        Get the maximum amount of partners a given member can have.

        Parameters
        ----------
        user : discord.Member
            The user that you want to get the max number of partners for.

        Returns
        -------
        int
            A number of partners that the user can have.
        """

        # See how many partners they're allowed normally (in regard to Patreon tier)
        marriagebot_perks: utils.MarriageBotPerks
        marriagebot_perks = await utils.get_marriagebot_perks(self.bot, user.id)  # type: ignore
        user_children_amount = marriagebot_perks.max_partners

        # Return the largest amount of partners they've been assigned
        # that's UNDER the global max partners as set in the config
        return min([
            max([
                user_children_amount,
                utils.TIER_NONE.max_partners,
            ]),
            utils.TIER_THREE.max_partners,
        ])

    @commands.context_command(name="Marry user")
    async def context_command_marry(self, ctx: vbu.Context, user: discord.User):
        command = self.marry
        await command.can_run(ctx)
        await ctx.invoke(command, target=user)  # type: ignore

    @commands.command(
        aliases=['propose'],
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="target",
                    description="The user you want to propose to.",
                    type=discord.ApplicationCommandOptionType.user,
                ),
            ],
        ),
    )
    @commands.defer()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @vbu.checks.bot_is_ready()
    @commands.guild_only()
    @commands.bot_has_permissions(send_messages=True)
    async def marry(
            self,
            ctx: vbu.Context,
            *,
            target: utils.converters.UnblockedMember):
        """
        Lets you propose to another Discord user.
        """

        # Get the family tree member objects
        family_guild_id = utils.get_family_guild_id(ctx)
        author_tree, target_tree = utils.FamilyTreeMember.get_multiple(
            ctx.author.id,
            target.id,
            guild_id=family_guild_id,
        )

        # Check they're not themselves
        if target.id == ctx.author.id:
            return await ctx.send("That's you. You can't marry yourself.")

        # Check they're not a bot
        if target.bot:
            if self.bot.user and target.id == self.bot.user.id:
                return await ctx.send("I think I could do better actually, but thank you!")
            return await ctx.send("That is a robot. Robots cannot consent to marriage.")

        # Lock those users
        re = await vbu.Redis.get_connection()
        try:
            lock = await utils.ProposalLock.lock(re, ctx.author.id, target.id)
        except utils.ProposalInProgress:
            return await ctx.send((
                "One of you is already waiting on a proposal - "
                "please try again later."
            ))

        # See if they're already related
        relation = author_tree.get_relation(target_tree)
        if relation and utils.guild_allows_incest(ctx) is False:
            await lock.unlock()
            return await ctx.send(
                (
                    f"Woah woah woah, it looks like you guys are already "
                    f"related! {target.mention} is your {relation}!"
                ),
                allowed_mentions=discord.AllowedMentions.only(ctx.author),
            )

        # See if we're already married
        author_partner_amount = await self.get_max_partners_for_member(author_tree)  # pyright: ignore
        if len(author_tree._partners) >= author_partner_amount:
            await lock.unlock()
            if author_partner_amount < utils.TIER_THREE.max_partners:
                comm = self.bot.get_command("info").mention  # pyright: ignore
                return await ctx.send(
                    (
                        f"Hey, {ctx.author.mention}, you're already at your "
                        "partner limit! You need to divorce someone (or donate "
                        f"at {comm}) to get another partner."
                    ),
                )
            return await ctx.send(
                (
                    f"Hey, {ctx.author.mention}, you're already at your partner limit! "
                    "You need to divorce someone to get another partner."
                ),
            )

        # See if the *target* is already married
        target_partner_amount = await self.get_max_partners_for_member(target_tree)  # pyright: ignore
        if len(target_tree._partners) >= target_partner_amount:
            await lock.unlock()
            return await ctx.send(
                (
                    f"Sorry, {ctx.author.mention}, it looks like "
                    f"{target.mention} is already at their partner limit \N{PENSIVE FACE} "
                    "If you both want to, you can have them divorce one of their "
                    "current partners."
                ),
                allowed_mentions=discord.AllowedMentions.only(ctx.author),
            )

        # Check the size of their trees
        # TODO I can make this a util because I'm going to use it a couple times
        max_family_members = utils.get_max_family_members(ctx)
        family_member_count = 0
        if author_tree.id not in self.bot.owner_ids:
            for _ in author_tree.span(add_parent=True, expand_upwards=True):
                if family_member_count >= max_family_members:
                    break
                family_member_count += 1
            for _ in target_tree.span(add_parent=True, expand_upwards=True):
                if family_member_count >= max_family_members:
                    break
                family_member_count += 1
            if family_member_count >= max_family_members:
                await lock.unlock()
                return await ctx.send(
                    (
                        f"If you added {target.mention} to your family, you'd "
                        f"have over {max_family_members} in your family. Sorry!"
                    ),
                    allowed_mentions=utils.only_mention(ctx.author),
                )

        # Set up the proposal
        try:
            result = await utils.send_proposal_message(
                ctx,
                target,
                (
                    f"Hey, {target.mention}, it would make {ctx.author.mention} "
                    "really happy if you would marry them. What do you say?"
                ),
            )
        except Exception:
            result = None
        if result is None:
            return await lock.unlock()

        # They said yes!
        async with vbu.Database() as db:
            try:
                await db.call(
                    """
                    INSERT INTO
                        marriages
                        (
                            user_id,
                            partner_id,
                            guild_id,
                            timestamp
                        )
                    VALUES
                        (
                            $1,
                            $2,
                            $3,
                            $4
                        )
                    """,
                    *sorted([ctx.author.id, target.id]), family_guild_id, dt.utcnow(),
                )
            except asyncpg.UniqueViolationError:
                await lock.unlock()
                self.bot.dispatch("recache_user", ctx.author, family_guild_id)
                self.bot.dispatch("recache_user", target, family_guild_id)
                return await result.messageable.send("I ran into an error saving your family data.")
        await vbu.embeddify(
            result.messageable,
            f"I'm happy to introduce {target.mention} into the family of {ctx.author.mention}!",
        )  # Keep allowed mentions on

        # Ping over redis
        author_tree.add_partner(target.id)
        target_tree.add_partner(ctx.author.id)
        await re.publish("TreeMemberUpdate", author_tree.to_json())
        await re.publish("TreeMemberUpdate", target_tree.to_json())
        await re.disconnect()
        await lock.unlock()

    @commands.command(
        application_command_meta=commands.ApplicationCommandMeta(),
    )
    @commands.defer()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @vbu.checks.bot_is_ready()
    @commands.guild_only()
    @commands.bot_has_permissions(send_messages=True, add_reactions=True)
    async def divorce(self, ctx: vbu.Context):
        """
        Divorce you from one of your partners.
        """

        # Get the user family tree member
        family_guild_id = utils.get_family_guild_id(ctx)
        user_tree = utils.FamilyTreeMember.get(ctx.author.id, guild_id=family_guild_id)

        # Make a list of options
        partner_options = []
        added_partner = set()
        for index, partner_tree in enumerate(user_tree.partners):
            if partner_tree.id in added_partner:
                continue
            added_partner.add(partner_tree.id)
            partner_name = await utils.DiscordNameManager.fetch_name_by_id(self.bot, partner_tree.id)
            partner_options.append(discord.ui.SelectOption(label=partner_name, value=f"DIVORCE {partner_tree.id}"))
            if index >= 25:
                return await ctx.send((
                    "I couldn't work out which of your partners you want to remove."
                ))

        # See if they don't have any children
        if not partner_options:
            return await ctx.send("You don't have any partners!")

        # Wait for them to pick one
        components = discord.ui.MessageComponents(discord.ui.ActionRow(
            discord.ui.SelectMenu(custom_id="DIVORCE_USER", options=partner_options),
        ))
        m = await vbu.embeddify(
            ctx,
            "Which of your partners would you like to divorce?",
            components=components,
        )

        # Make our check
        def check(interaction: discord.Interaction):
            assert interaction.message
            if interaction.message.id != m.id:
                return False
            assert interaction.user
            if interaction.user.id != ctx.author.id:
                self.bot.loop.create_task(interaction.response.send_message("You can't respond to this message!", ephemeral=True))
                return False
            return True
        try:
            interaction = await self.bot.wait_for("component_interaction", check=check, timeout=60)
            await interaction.response.defer_update()
        except asyncio.TimeoutError:
            return await ctx.send("Timed out asking for which partner you want to divorce :<")

        # Get the child's ID that they selected
        target = int(interaction.values[0][len("DIVORCE "):])

        # Get the family tree member objects
        partner_tree = utils.FamilyTreeMember.get(target, guild_id=family_guild_id)
        partner_name = await utils.DiscordNameManager.fetch_name_by_id(self.bot, partner_tree.id)

        # Make sure they're actually children
        if partner_tree.id not in user_tree._partners:
            return await ctx.send(
                f"It doesn't look like **{utils.escape_markdown(partner_name)}** is one of your partners!",
                allowed_mentions=discord.AllowedMentions.none(),
            )

        # See if they're sure
        try:
            result = await utils.send_proposal_message(
                ctx, ctx.author,
                f"Are you sure you want to divorce **{utils.escape_markdown(partner_name)}**, {ctx.author.mention}?",
                timeout_message=f"Timed out making sure you want to divorce, {ctx.author.mention} :<",
                cancel_message="Alright, I've cancelled your divorce!",
            )
        except Exception:
            result = None
        if result is None:
            return

        # Remove from cache
        user_tree.remove_partner(partner_tree.id)
        partner_tree.remove_partner(user_tree.id)

        # Remove from redis
        async with vbu.Redis() as re:
            await re.publish("TreeMemberUpdate", user_tree.to_json())
            await re.publish("TreeMemberUpdate", partner_tree.to_json())

        # Remove from database
        async with vbu.Database() as db:
            await db(
                """
                DELETE FROM
                    marriages
                WHERE
                    (
                        user_id = $1
                        AND partner_id = $2
                    )
                    OR (
                        user_id = $2
                        AND partner_id = $1
                    )
                    AND guild_id = $3
                """,
                *sorted([partner_tree.id, ctx.author.id]), family_guild_id,
            )

        # And we're done
        await vbu.embeddify(
            result.messageable,
            f"You've successfully divorced **{utils.escape_markdown(partner_name)}** :c",
            allowed_mentions=discord.AllowedMentions.none(),
        )


def setup(bot: types.Bot):
    x = Marriage(bot)
    bot.add_cog(x)
