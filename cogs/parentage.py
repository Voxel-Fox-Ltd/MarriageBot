from __future__ import annotations

import typing
import asyncio
from datetime import datetime as dt

import asyncpg
import discord
from discord.ext import commands, vbu

from cogs import utils


class Parentage(vbu.Cog[utils.types.Bot]):

    async def get_max_children_for_member(
            self,
            guild: discord.Guild,
            user: discord.Member) -> int:
        """
        Get the maximum amount of children a given member can have.

        Parameters
        ----------
        guild : discord.Guild
            The guild that the user is in.
        user : discord.Member
            The user that you want to get the max number of children for.

        Returns
        -------
        int
            A number of children that the user can have.
        """

        # Bots can do what they want
        if user.bot:
            return 5

        # See how many children they're allowed with Gold
        gold_children_amount = 0
        if self.bot.config.get('is_server_specific', False):
            guild_max_children = self.bot.guild_settings[guild.id].get('max_children')
            if guild_max_children:
                gold_children_amount = max([
                    amount if discord.Object(role_id) in user.roles else 0
                    for role_id, amount in guild_max_children.items()
                ])

        # See how many children they're allowed normally (in regard to Patreon tier)
        marriagebot_perks: utils.MarriageBotPerks
        marriagebot_perks = await utils.get_marriagebot_perks(self.bot, user.id)  # type: ignore
        user_children_amount = marriagebot_perks.max_children

        # Return the largest amount of children they've been assigned
        # that's UNDER the global max children as set in the config
        return min([
            max([
                gold_children_amount,
                user_children_amount,
                utils.TIER_NONE.max_children,
            ]),
            utils.TIER_THREE.max_children,
        ])

    @commands.context_command(name="Make user your parent")
    async def context_command_makeparent(
            self,
            ctx: vbu.Context,
            user: utils.converters.UnblockedMember):
        command = self.makeparent
        await command.can_run(ctx)
        await ctx.invoke(command, target=user)  # type: ignore

    @commands.command(
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="target",
                    description="The user you want to make your parent.",
                    type=discord.ApplicationCommandOptionType.user,
                ),
            ],
        ),
    )
    @commands.defer()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @vbu.checks.bot_is_ready()
    @commands.guild_only()
    @commands.bot_has_permissions(send_messages=True, add_reactions=True)
    async def makeparent(
            self,
            ctx: vbu.Context,
            *,
            target: utils.converters.UnblockedMember):
        """
        Picks a user that you want to be your parent.
        """

        # Variables we're gonna need for later
        family_guild_id = utils.get_family_guild_id(ctx)
        author_tree, target_tree = utils.FamilyTreeMember.get_multiple(
            ctx.author.id,
            target.id,
            guild_id=family_guild_id,
        )

        # Check they're not themselves
        if target.id == ctx.author.id:
            return await ctx.send("That's you. You can't make yourself your parent.")

        # Check they're not a bot
        if self.bot.user and target.id == self.bot.user.id:
            return await ctx.send("I think I could do better actually, but thank you!")

        # Lock those users
        re = await vbu.Redis.get_connection()
        try:
            lock = await utils.ProposalLock.lock(re, ctx.author.id, target.id)
        except utils.ProposalInProgress:
            return await ctx.send("One of you is already waiting on a proposal - please try again later.")

        # See if the *target* is already married
        if author_tree.parent:
            await lock.unlock()
            return await ctx.send(
                f"Hey! {ctx.author.mention}, you already have a parent \N{ANGRY FACE}",
                allowed_mentions=utils.only_mention(ctx.author),
            )

        # See if we're already married
        if ctx.author.id in target_tree._children:
            await lock.unlock()
            return await ctx.send(
                f"Hey isn't {target.mention} already your child? \N{FACE WITH ROLLING EYES}",
                allowed_mentions=utils.only_mention(ctx.author),
            )

        # See if they're already related
        relation = author_tree.get_relation(target_tree)
        if relation and utils.guild_allows_incest(ctx) is False:
            await lock.unlock()
            return await ctx.send(
                f"Woah woah woah, it looks like you guys are already related! {target.mention} is your {relation}!",
                allowed_mentions=utils.only_mention(ctx.author),
            )

        # Manage children
        assert ctx.guild
        children_amount = await self.get_max_children_for_member(ctx.guild, target)
        if len(target_tree._children) >= children_amount:
            return await ctx.send(
                f"They're currently at the maximum amount of children they can have - see `{ctx.prefix}perks` for more information.",
            )

        # Check the size of their trees
        max_family_members = utils.get_max_family_members(ctx)
        family_member_count = 0
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
                f"If you added {target.mention} to your family, you'd have over {max_family_members} in your family. Sorry!",
                allowed_mentions=utils.only_mention(ctx.author),
            )

        # Set up the proposal
        try:
            result = await utils.send_proposal_message(
                ctx, target,
                f"Hey, {target.mention}, {ctx.author.mention} wants to be your child! What do you think?",
                allow_bots=True,
            )
        except Exception:
            result = None
        if result is None:
            return await lock.unlock()

        # Database it up
        dispatch_tmu: bool = True
        async with vbu.Database() as db:
            try:
                await db(
                    """INSERT INTO parents (parent_id, child_id, guild_id, timestamp) VALUES ($1, $2, $3, $4)""",
                    target.id, ctx.author.id, family_guild_id, dt.utcnow(),
                )
            except asyncpg.UniqueViolationError:
                dispatch_tmu = False
                self.bot.dispatch("recache_user", ctx.author, family_guild_id)
                self.bot.dispatch("recache_user", target, family_guild_id)
        await vbu.embeddify(
            result.messageable,
            f"I'm happy to introduce {ctx.author.mention} as your child, {target.mention}!",
        )

        # And we're done
        target_tree._children.append(author_tree.id)
        author_tree._parent = target.id
        if dispatch_tmu:
            await re.publish("TreeMemberUpdate", author_tree.to_json())
            await re.publish("TreeMemberUpdate", target_tree.to_json())
        await re.disconnect()
        await lock.unlock()

    @commands.context_command(name="Adopt user")
    async def context_command_adopt(self, ctx: vbu.Context, user: utils.converters.UnblockedMember):
        command = self.adopt
        await command.can_run(ctx)
        await ctx.invoke(command, target=user)  # type: ignore

    @commands.command(
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="target",
                    description="The user you want to adopt.",
                    type=discord.ApplicationCommandOptionType.user,
                ),
            ],
        ),
    )
    @commands.defer()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @vbu.checks.bot_is_ready()
    @commands.guild_only()
    @commands.bot_has_permissions(send_messages=True, add_reactions=True)
    async def adopt(self, ctx: vbu.Context, *, target: utils.converters.UnblockedMember):
        """
        Adopt another user into your family.
        """

        # Variables we're gonna need for later
        family_guild_id = utils.get_family_guild_id(ctx)
        author_tree, target_tree = utils.FamilyTreeMember.get_multiple(ctx.author.id, target.id, guild_id=family_guild_id)

        # Check they're not themselves
        if target.id == ctx.author.id:
            return await ctx.send("That's you. You can't adopt yourself.")

        # Check they're not a bot
        if target.bot:
            if self.bot.user and target.id == self.bot.user.id:
                return await ctx.send("I think I could do better actually, but thank you!")
            return await ctx.send("That is a robot. Robots cannot consent to adoption.")

        # Lock those users
        re = await vbu.Redis.get_connection()
        try:
            lock = await utils.ProposalLock.lock(re, ctx.author.id, target.id)
        except utils.ProposalInProgress:
            return await ctx.send("One of you is already waiting on a proposal - please try again later.")

        # See if the *target* is already married
        if target_tree.parent:
            await lock.unlock()
            return await ctx.send(
                f"Sorry, {ctx.author.mention}, it looks like {target.mention} already has a parent \N{PENSIVE FACE}",
                allowed_mentions=utils.only_mention(ctx.author),
            )

        # See if we're already married
        if target.id in author_tree._children:
            await lock.unlock()
            return await ctx.send(
                f"Hey, {ctx.author.mention}, they're already your child \N{FACE WITH ROLLING EYES}",
                allowed_mentions=utils.only_mention(ctx.author),
            )

        # See if they're already related
        relation = author_tree.get_relation(target_tree)
        if relation and utils.guild_allows_incest(ctx) is False:
            await lock.unlock()
            return await ctx.send(
                f"Woah woah woah, it looks like you guys are already related! {target.mention} is your {relation}!",
                allowed_mentions=utils.only_mention(ctx.author),
            )

        # Manage children
        assert ctx.guild
        children_amount = await self.get_max_children_for_member(ctx.guild, ctx.author)
        if len(author_tree._children) >= children_amount:
            return await ctx.send(
                f"You're currently at the maximum amount of children you can have - see `{ctx.prefix}perks` for more information.",
            )

        # Check the size of their trees
        max_family_members = utils.get_max_family_members(ctx)
        family_member_count = 0
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
                f"If you added {target.mention} to your family, you'd have over {max_family_members} in your family. Sorry!",
                allowed_mentions=utils.only_mention(ctx.author),
            )

        # Set up the proposal
        try:
            result = await utils.send_proposal_message(
                ctx, target,
                f"Hey, {target.mention}, {ctx.author.mention} wants to adopt you! What do you think?",
            )
        except Exception:
            result = None
        if result is None:
            return await lock.unlock()

        # Database it up
        dispatch_tmu: bool = True
        async with vbu.Database() as db:
            try:
                await db(
                    """
                    INSERT INTO
                        parents
                        (
                            parent_id,
                            child_id,
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
                    ctx.author.id, target.id, family_guild_id, dt.utcnow(),
                )
            except asyncpg.UniqueViolationError:
                dispatch_tmu = False
                self.bot.dispatch("recache_user", ctx.author, family_guild_id)
                self.bot.dispatch("recache_user", target, family_guild_id)
        await vbu.embeddify(
            result.messageable,
            f"I'm happy to introduce {ctx.author.mention} as your parent, {target.mention}!",
        )

        # And we're done
        author_tree._children.append(target.id)
        target_tree._parent = author_tree.id
        if dispatch_tmu:
            await re.publish('TreeMemberUpdate', author_tree.to_json())
            await re.publish('TreeMemberUpdate', target_tree.to_json())
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
    async def disown(self, ctx: vbu.Context):
        """
        Remove someone from being your child.
        """

        # Get the user family tree member
        family_guild_id = utils.get_family_guild_id(ctx)
        user_tree = utils.FamilyTreeMember.get(ctx.author.id, guild_id=family_guild_id)

        # Make a list of options
        child_options = []
        added_children = set()
        for index, child_tree in enumerate(user_tree.children):
            if child_tree.id in added_children:
                continue
            added_children.add(child_tree.id)
            child_name = await utils.DiscordNameManager.fetch_name_by_id(self.bot, child_tree.id)
            child_options.append(discord.ui.SelectOption(label=child_name, value=f"DISOWN {child_tree.id}"))
            if index >= 25:
                return await ctx.send((
                    "I couldn't work out which of your children you wanted to disown. "
                    "You can ping or use their ID to disown them."
                ))

        # See if they don't have any children
        if not child_options:
            return await ctx.send("You don't have any children!")

        # Wait for them to pick one
        components = discord.ui.MessageComponents(discord.ui.ActionRow(
            discord.ui.SelectMenu(custom_id="DISOWN_USER", options=child_options),
        ))
        m = await vbu.embeddify(
            ctx,
            "Which of your children would you like to disown?",
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
            return await ctx.send("Timed out asking for which child you want to disown :<")

        # Get the child's ID that they selected
        target = int(interaction.values[0][len("DISOWN "):])

        # Get the family tree member objects
        child_tree = utils.FamilyTreeMember.get(target, guild_id=family_guild_id)
        child_name = await utils.DiscordNameManager.fetch_name_by_id(self.bot, child_tree.id)

        # Make sure they're actually children
        if child_tree.id not in user_tree._children:
            return await ctx.send(
                f"It doesn't look like **{utils.escape_markdown(child_name)}** is one of your children!",
                allowed_mentions=discord.AllowedMentions.none(),
            )

        # See if they're sure
        try:
            result = await utils.send_proposal_message(
                ctx, ctx.author,
                f"Are you sure you want to disown **{utils.escape_markdown(child_name)}**, {ctx.author.mention}?",
                timeout_message=f"Timed out making sure you want to disown, {ctx.author.mention} :<",
                cancel_message="Alright, I've cancelled your disown!",
            )
        except Exception:
            result = None
        if result is None:
            return

        # Remove from cache
        user_tree.remove_child(child_tree.id)
        child_tree.parent = None

        # Remove from redis
        async with vbu.Redis() as re:
            await re.publish("TreeMemberUpdate", user_tree.to_json())
            await re.publish("TreeMemberUpdate", child_tree.to_json())

        # Remove from database
        async with vbu.Database() as db:
            await db(
                """
                DELETE FROM
                    parents
                WHERE
                    child_id = $1
                    AND parent_id = $2
                    AND guild_id = $3
                """,
                child_tree.id, ctx.author.id, family_guild_id,
            )

        # And we're done
        await vbu.embeddify(
            result.messageable,
            f"You've successfully disowned **{utils.escape_markdown(child_name)}** :c",
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @commands.command(
        aliases=['eman', 'emancipate', 'runawayfromhome'],
        application_command_meta=commands.ApplicationCommandMeta(),
    )
    @commands.defer()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @vbu.checks.bot_is_ready()
    @commands.guild_only()
    @commands.bot_has_permissions(send_messages=True, add_reactions=True)
    async def runaway(self, ctx: vbu.Context):
        """
        Removes your parent.
        """

        # Get the family tree member objects
        family_guild_id = utils.get_family_guild_id(ctx)
        user_tree = utils.FamilyTreeMember.get(ctx.author.id, guild_id=family_guild_id)

        # Make sure they're the child of the instigator
        parent_tree = user_tree.parent
        if not parent_tree:
            return await ctx.send("You don't have a parent right now :<")

        # See if they're sure
        try:
            result = await utils.send_proposal_message(
                ctx, ctx.author,
                f"Are you sure you want to leave your parent, {ctx.author.mention}?",
                timeout_message=f"Timed out making sure you want to emancipate, {ctx.author.mention} :<",
                cancel_message="Alright, I've cancelled your emancipation!",
            )
        except Exception:
            result = None
        if result is None:
            return

        # Remove family caching
        user_tree.parent = None
        parent_tree.remove_child(ctx.author.id)

        # Ping them off over reids
        async with vbu.Redis() as re:
            await re.publish("TreeMemberUpdate", user_tree.to_json())
            await re.publish("TreeMemberUpdate", parent_tree.to_json())

        # Remove their relationship from the database
        async with vbu.Database() as db:
            await db(
                """DELETE FROM parents WHERE parent_id=$1 AND child_id=$2 AND guild_id=$3""",
                parent_tree.id, ctx.author.id, family_guild_id,
            )

        # And we're done
        parent_name = await utils.DiscordNameManager.fetch_name_by_id(self.bot, parent_tree.id)
        await vbu.embeddify(
            result.messageable,
            f"You no longer have **{utils.escape_markdown(parent_name)}** as a parent :c",
        )

    @commands.command(
        application_command_meta=commands.ApplicationCommandMeta(),
    )
    @commands.defer()
    @utils.checks.has_donator_perks("can_run_disownall")
    @commands.cooldown(1, 3, commands.BucketType.user)
    @vbu.checks.bot_is_ready()
    @commands.guild_only()
    @commands.bot_has_permissions(send_messages=True, add_reactions=True)
    async def disownall(self, ctx: vbu.Context):
        """
        Disowns all of your children.
        """

        # Get the family tree member objects
        family_guild_id = utils.get_family_guild_id(ctx)
        user_tree = utils.FamilyTreeMember.get(ctx.author.id, guild_id=family_guild_id)
        child_trees = list(user_tree.children)
        if not child_trees:
            return await ctx.send("You don't have any children to disown .-.")

        # See if they're sure
        try:
            result = await utils.send_proposal_message(
                ctx, ctx.author,
                f"Are you sure you want to disown all your children, {ctx.author.mention}?",
                timeout_message=f"Timed out making sure you want to disownall, {ctx.author.mention} :<",
                cancel_message="Alright, I've cancelled your disownall!",
            )
        except Exception:
            result = None
        if result is None:
            return

        # Disown em
        for child in child_trees:
            child._parent = None
        user_tree._children = []

        # Save em
        async with vbu.Database() as db:
            await db(
                """
                DELETE FROM
                    parents
                WHERE
                    parent_id = $1
                    AND guild_id = $2
                    AND child_id = ANY($3::BIGINT[])
                """,
                ctx.author.id, family_guild_id, [child.id for child in child_trees],
            )

        # Redis em
        async with vbu.Redis() as re:
            for person in child_trees + [user_tree]:
                await re.publish("TreeMemberUpdate", person.to_json())

        # Output to user
        await vbu.embeddify(
            result.messageable,
            "You've sucessfully disowned all of your children :c",
        )


def setup(bot: utils.types.Bot):
    x = Parentage(bot)
    bot.add_cog(x)
