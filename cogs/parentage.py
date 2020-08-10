from datetime import datetime as dt

import asyncpg
import discord
from discord.ext import commands

from cogs import utils


class Parentage(utils.Cog):

    async def get_max_children_for_member(self, guild:discord.Guild, user:discord.Member):
        """Get the maximum amount of children a given member can have"""

        # See how many children they're allowed with Gold
        gold_children_amount = 0
        if self.bot.is_server_specific:
            guild_max_children = self.bot.guild_settings[guild.id]['max_children']
            if guild_max_children:
                gold_children_amount = max([
                    amount if int(role_id) in user._roles else 0 for role_id, amount in guild_max_children.items()
                ])

        # See how many children they're allowed normally (in regard to Patreon tier)
        normal_children_amount = await utils.checks.has_donator_perks_predicate(self.bot, "max_children", user)

        # Return the largest amount of children they've been assigned that's UNDER the global max children as set in the config
        return min([
            max([
                gold_children_amount,
                normal_children_amount,
                min([i['max_children'] for i in self.bot.config['role_perks'].values()])
            ]),
            max([i['max_children'] for i in self.bot.config['role_perks'].values()])
        ])

    @commands.command(cls=utils.Command)
    @utils.cooldown.cooldown(1, 5, commands.BucketType.user)
    @utils.checks.bot_is_ready()
    @commands.bot_has_permissions(send_messages=True)
    async def makeparent(self, ctx:utils.Context, *, target:utils.converters.UnblockedMember):
        """Picks a user that you want to be your parent"""

        # Variables we're gonna need for later
        instigator = ctx.author
        instigator_tree = utils.FamilyTreeMember.get(instigator.id, ctx.family_guild_id)
        target_tree = utils.FamilyTreeMember.get(target.id, ctx.family_guild_id)

        # Manage output strings
        text_processor = utils.random_text.RandomText('makeparent', instigator, target)
        text = text_processor.process()
        if text:
            return await ctx.send(text)

        # See if our user already has a parent
        if instigator_tree._parent:
            return await ctx.send(text_processor.instigator_is_unqualified())

        # See if they're already related
        async with ctx.channel.typing():
            relation = instigator_tree.get_relation(target_tree)
        if relation and not self.bot.allows_incest(ctx.guild.id):
            return await ctx.send(text_processor.target_is_family())

        # Manage children
        if ctx.original_author_id not in self.bot.owner_ids:
            children_amount = await self.get_max_children_for_member(ctx.guild, target)
            if len(target_tree._children) >= children_amount:
                return await ctx.send("They're currently at the maximum amount of children you can have - see `m!perks` for more information.")

        # Check the size of their trees
        if ctx.original_author_id not in self.bot.owner_ids:
            max_family_members = self.bot.get_max_family_members(ctx.guild)
            async with ctx.channel.typing():
                if instigator_tree.family_member_count + target_tree.family_member_count > max_family_members:
                    return await ctx.send(f"If you added {target.mention} to your family, you'd have over {max_family_members} in your family, so I can't allow you to do that. Sorry!")

        # Valid request - ask the other person
        if not target.bot:
            await ctx.send(text_processor.valid_target())
        await self.bot.proposal_cache.add(instigator, target, 'MAKEPARENT')
        check = utils.AcceptanceCheck(target.id, ctx.channel.id)
        try:
            await check.wait_for_response(self.bot)
        except utils.AcceptanceCheck.TIMEOUT:
            return await ctx.send(text_processor.request_timeout(), ignore_error=True)

        # They said no
        if check.response == 'NO':
            await self.bot.proposal_cache.remove()
            return await ctx.send(text_processor.request_denied(), ignore_error=True)

        # They said yes
        async with self.bot.database() as db:
            try:
                await db('INSERT INTO parents (child_id, parent_id, guild_id, timestamp) VALUES ($1, $2, $3, $4)', instigator.id, target.id, ctx.family_guild_id, dt.utcnow())
            except asyncpg.UniqueViolationError:
                return await ctx.send("I ran into an error saving your family data - please try again later.")
        await ctx.send(text_processor.request_accepted(), ignore_error=True)

        # Cache
        instigator_tree._parent = target.id
        target_tree._children.append(instigator.id)

        # Ping em off over redis
        async with self.bot.redis() as re:
            await re.publish_json('TreeMemberUpdate', instigator_tree.to_json())
            await re.publish_json('TreeMemberUpdate', target_tree.to_json())

        # Uncache
        await self.bot.proposal_cache.remove(instigator, target)

    @commands.command(cls=utils.Command)
    @utils.cooldown.cooldown(1, 5, commands.BucketType.user)
    @utils.checks.bot_is_ready()
    @commands.bot_has_permissions(send_messages=True)
    async def adopt(self, ctx:utils.Context, *, target:utils.converters.UnblockedMember):
        """Adopt another user into your family"""

        # Variables we're gonna need for later
        instigator = ctx.author
        instigator_tree = utils.FamilyTreeMember.get(instigator.id, ctx.family_guild_id)
        target_tree = utils.FamilyTreeMember.get(target.id, ctx.family_guild_id)

        # Manage output strings
        text_processor = utils.random_text.RandomText('adopt', instigator, target)
        text = text_processor.process()
        if text:
            return await ctx.send(text)

        # See if our user already has a parent
        if target_tree._parent:
            return await ctx.send(text_processor.target_is_unqualified())

        # See if the target is a bot
        if target.bot:
            return await ctx.send(text_processor.target_is_bot())

        # See if they're already related
        async with ctx.channel.typing():
            relation = instigator_tree.get_relation(target_tree)
        if relation and not self.bot.allows_incest(ctx.guild.id):
            return await ctx.send(text_processor.target_is_family())

        # Manage children
        if ctx.original_author_id not in self.bot.owner_ids:
            children_amount = await self.get_max_children_for_member(ctx.guild, ctx.author)
            if len(instigator_tree._children) >= children_amount:
                return await ctx.send(f"You're currently at the maximum amount of children you can have - see `{ctx.prefix}perks` for more information.")

        # Check the size of their trees
        if ctx.original_author_id not in self.bot.owner_ids:
            max_family_members = self.bot.get_max_family_members(ctx.guild)
            async with ctx.channel.typing():
                if instigator_tree.family_member_count + target_tree.family_member_count > max_family_members:
                    return await ctx.send(f"If you added {target.mention} to your family, you'd have over {max_family_members} in your family, so I can't allow you to do that. Sorry!")

        # No parent, send request
        await ctx.send(text_processor.valid_target())
        await self.bot.proposal_cache.add(instigator, target, 'ADOPT')

        # Wait for a response
        check = utils.AcceptanceCheck(target.id, ctx.channel.id)
        try:
            await check.wait_for_response(self.bot)
        except utils.AcceptanceCheck.TIMEOUT:
            return await ctx.send(text_processor.request_timeout(), ignore_error=True)

        # Valid response recieved, see what their answer was
        if check.response == 'NO':
            await self.bot.proposal_cache.remove(instigator, target)
            return await ctx.send(text_processor.request_denied(), ignore_error=True)

        # Database it up
        async with self.bot.database() as db:
            try:
                await db('INSERT INTO parents (parent_id, child_id, guild_id, timestamp) VALUES ($1, $2, $3, $4)', instigator.id, target.id, ctx.family_guild_id, dt.utcnow())
            except asyncpg.UniqueViolationError:
                return await ctx.send("I ran into an error saving your family data - please try again later.")

        # Add family caching
        instigator_tree._children.append(target.id)
        target_tree._parent = instigator_tree.id

        # Ping em off over redis
        async with self.bot.redis() as re:
            await re.publish_json('TreeMemberUpdate', instigator_tree.to_json())
            await re.publish_json('TreeMemberUpdate', target_tree.to_json())

        # Uncache
        await self.bot.proposal_cache.remove(instigator, target)

        # Output to user
        await ctx.send(text_processor.request_accepted(), ignore_error=True)

    @commands.command(aliases=['abort'], cls=utils.Command)
    @utils.cooldown.cooldown(1, 5, commands.BucketType.user)
    @utils.checks.bot_is_ready()
    @commands.bot_has_permissions(send_messages=True)
    async def disown(self, ctx:utils.Context, *, target:utils.converters.UserID):
        """Lets you remove a user from being your child"""

        # Manage output strings
        text_processor = utils.random_text.RandomText('disown', ctx.author, self.bot.get_user(target))

        # Variables we're gonna need for later
        instigator = ctx.author
        instigator_tree = utils.FamilyTreeMember.get(instigator.id, ctx.family_guild_id)
        target_tree = utils.FamilyTreeMember.get(target, ctx.family_guild_id)

        # Make sure they're the child of the instigator
        if target_tree.id not in instigator_tree._children:
            return await ctx.send(text_processor.instigator_is_unqualified())

        # Oh hey they are - remove from database
        async with self.bot.database() as db:
            await db('DELETE FROM parents WHERE child_id=$1 AND parent_id=$2 AND guild_id=$3', target_tree.id, instigator.id, instigator_tree._guild_id)
        await ctx.send(text_processor.valid_target(), ignore_error=True)

        # Remove family caching
        instigator_tree._children.remove(target_tree.id)
        target_tree._parent = None

        # Ping em off over redis
        async with self.bot.redis() as re:
            await re.publish_json('TreeMemberUpdate', instigator_tree.to_json())
            await re.publish_json('TreeMemberUpdate', target_tree.to_json())

    @commands.command(aliases=['eman', 'runaway', 'runawayfromhome'], cls=utils.Command)
    @utils.cooldown.cooldown(1, 5, commands.BucketType.user)
    @utils.checks.bot_is_ready()
    @commands.bot_has_permissions(send_messages=True)
    async def emancipate(self, ctx:utils.Context):
        """Removes your parent"""

        # Variables we're gonna need for later
        instigator = ctx.author
        instigator_tree = utils.FamilyTreeMember.get(instigator.id, ctx.family_guild_id)

        # Manage output strings
        text_processor = utils.random_text.RandomText('emancipate', ctx.author, self.bot.get_user(instigator_tree._parent))

        # Make sure they're the child of the instigator
        if not instigator_tree._parent:
            return await ctx.send(text_processor.instigator_is_unqualified())

        # They do have a parent, yes
        target_tree = instigator_tree.parent

        # Remove family caching
        instigator_tree._parent = None
        target_tree._children.remove(instigator.id)

        # Ping em off over redis
        async with self.bot.redis() as re:
            await re.publish_json('TreeMemberUpdate', instigator_tree.to_json())
            await re.publish_json('TreeMemberUpdate', target_tree.to_json())

        # Oh hey they are - remove from database
        async with self.bot.database() as db:
            await db('DELETE FROM parents WHERE parent_id=$1 AND child_id=$2 AND guild_id=$3', target_tree.id, instigator.id, instigator_tree._guild_id)
        await ctx.send(text_processor.valid_target())

    @commands.command(cls=utils.Command)
    @utils.checks.has_donator_perks("disownall_command")
    @commands.bot_has_permissions(send_messages=True)
    async def disownall(self, ctx:utils.Context):
        """Disowns all of your children"""

        # Get their children
        user_tree = utils.FamilyTreeMember.get(ctx.author.id, ctx.family_guild_id)
        children = user_tree.children[:]
        if not children:
            return await ctx.send("You don't have any children to disown .-.")

        # Disown em
        for child in children:
            child._parent = None
        user_tree._children = []

        # Save em
        async with self.bot.database() as db:
            for child in children:
                await db('DELETE FROM parents WHERE parent_id=$1 AND child_id=$2 AND guild_id=$3', user_tree.id, child.id, user_tree._guild_id)

        # Redis em
        async with self.bot.redis() as re:
            for person in children + [user_tree]:
                await re.publish_json('TreeMemberUpdate', person.to_json())

        # Output to user
        await ctx.send("You've sucessfully disowned all of your children.")


def setup(bot:utils.Bot):
    x = Parentage(bot)
    bot.add_cog(x)
