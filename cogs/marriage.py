from datetime import datetime as dt

import asyncpg
import discord
from discord.ext import commands
import voxelbotutils as utils

from cogs import utils as localutils


class Marriage(utils.Cog):

    @utils.command(aliases=['marry'])
    @utils.cooldown.no_raise_cooldown(1, 3, commands.BucketType.user)
    @utils.checks.bot_is_ready()
    @commands.bot_has_permissions(send_messages=True, add_reactions=True)
    async def propose(self, ctx:utils.Context, *, target:localutils.converters.UnblockedMember):
        """
        Lets you propose to another Discord user.
        """

        # Get the family tree member objects
        family_guild_id = localutils.get_family_guild_id(ctx)
        author_tree, target_tree = localutils.FamilyTreeMember.get_multiple(ctx.author.id, target.id, guild_id=family_guild_id)

        # Check they're not themselves
        if target.id == ctx.author.id:
            return await ctx.send("That's you. You can't marry yourself.")

        # Check they're not a bot
        if target.bot:
            if target.id == self.bot.user.id:
                return await ctx.send("I think I could do better actually, but thank you!")
            return await ctx.send("That is a robot. Robots cannot consent to marriage.")

        # Lock those users
        re = await self.bot.redis.get_connection()
        try:
            lock = await localutils.ProposalLock.lock(re, ctx.author.id, target.id)
        except localutils.ProposalInProgress:
            return await ctx.send("Aren't you popular! One of you is already waiting on a proposal - please try again later.")

        # See if we're already married
        if author_tree._partner:
            await lock.unlock()
            return await ctx.send(
                f"Hey, {ctx.author.mention}, you're already married! Try divorcing your partner first \N{FACE WITH ROLLING EYES}",
                allowed_mentions=localutils.only_mention(ctx.author),
            )

        # See if the *target* is already married
        if target_tree._partner:
            await lock.unlock()
            return await ctx.send(
                f"Sorry, {ctx.author.mention}, it looks like {target.mention} is already married \N{PENSIVE FACE}",
                allowed_mentions=localutils.only_mention(ctx.author),
            )

        # See if they're already related
        async with ctx.channel.typing():
            relation = author_tree.get_relation(target_tree)
        if relation and localutils.guild_allows_incest(ctx) is False:
            await lock.unlock()
            return await ctx.send(
                f"Woah woah woah, it looks like you guys are already related! {target.mention} is your {relation}!",
                allowed_mentions=localutils.only_mention(ctx.author),
            )

        # Check the size of their trees
        # TODO I can make this a util because I'm going to use it a couple times
        max_family_members = localutils.get_max_family_members(ctx)
        async with ctx.channel.typing():
            family_member_count = 0
            for i in author_tree.span(add_parent=True, expand_upwards=True):
                if family_member_count >= max_family_members:
                    break
                family_member_count += 1
            for i in target_tree.span(add_parent=True, expand_upwards=True):
                if family_member_count >= max_family_members:
                    break
                family_member_count += 1
            if family_member_count >= max_family_members:
                await lock.unlock()
                return await ctx.send(
                    f"If you added {target.mention} to your family, you'd have over {max_family_members} in your family. Sorry!",
                    allowed_mentions=localutils.only_mention(ctx.author),
                )

        # Set up the proposal
        try:
            result = await localutils.send_proposal_message(
                ctx, target,
                f"Hey, {target.mention}, it would make {ctx.author.mention} really happy if you would marry them. What do you say?",
            )
        except Exception:
            result = None
        if result is None:
            return await lock.unlock()

        # They said yes!
        async with self.bot.database() as db:
            try:
                await db.start_transaction()
                await db(
                    "INSERT INTO marriages (user_id, partner_id, guild_id, timestamp) VALUES ($1, $2, $3, $4), ($2, $1, $3, $4)",
                    ctx.author.id, target.id, family_guild_id, dt.utcnow(),
                )
                await db.commit_transaction()
            except asyncpg.UniqueViolationError:
                await lock.unlock()
                return await result.ctx.send("I ran into an error saving your family data.")
        await result.ctx.send(f"I'm happy to introduce {target.mention} into the family of {ctx.author.mention}!")

        # Ping over redis
        author_tree._partner = target.id
        target_tree._partner = ctx.author.id
        await re.publish('TreeMemberUpdate', author_tree.to_json())
        await re.publish('TreeMemberUpdate', target_tree.to_json())
        await re.disconnect()
        await lock.unlock()

    @utils.command()
    @utils.cooldown.no_raise_cooldown(1, 3, commands.BucketType.user)
    @utils.checks.bot_is_ready()
    @commands.bot_has_permissions(send_messages=True, add_reactions=True)
    async def divorce(self, ctx:utils.Context):
        """
        Divorces you from your current partner.
        """

        # Get the family tree member objects
        family_guild_id = localutils.get_family_guild_id(ctx)
        author_tree = localutils.FamilyTreeMember.get(ctx.author.id, guild_id=family_guild_id)

        # See if they're married
        target_tree = author_tree.partner
        if not target_tree:
            return await ctx.send("It doesn't look like you're married yet!")

        # See if they're sure
        try:
            result = await localutils.send_proposal_message(
                ctx, ctx.author,
                f"Are you sure you want to divorce your partner, {ctx.author.mention}?",
                timeout_message=f"Timed out making sure you want to divorce, {ctx.author.mention} :<",
                cancel_message="Alright, I've cancelled your divorce!",
            )
        except Exception:
            result = None
        if result is None:
            return

        # Remove them from the database
        async with self.bot.database() as db:
            await db(
                """DELETE FROM marriages WHERE (user_id=$1 OR user_id=$2) AND guild_id=$3""",
                ctx.author.id, target_tree.id, family_guild_id,
            )
        partner_name = await localutils.DiscordNameManager.fetch_name_by_id(self.bot, author_tree._partner)
        await result.ctx.send(
            f"You've successfully divorced **{localutils.escape_markdown(partner_name)}** :c",
            allowed_mentions=discord.AllowedMentions.none(),
        )

        # Ping over redis
        author_tree._partner = None
        target_tree._partner = None
        async with self.bot.redis() as re:
            await re.publish('TreeMemberUpdate', author_tree.to_json())
            await re.publish('TreeMemberUpdate', target_tree.to_json())


def setup(bot:utils.Bot):
    x = Marriage(bot)
    bot.add_cog(x)
