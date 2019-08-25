from datetime import datetime as dt
from typing import Union

from discord import User
from discord.ext.commands import command, Context, cooldown
from discord.ext.commands import MissingPermissions, MissingRequiredArgument, BadArgument, CommandOnCooldown, MissingRole
from discord.ext.commands.cooldowns import BucketType

from cogs.utils.custom_bot import CustomBot
from cogs.utils.family_tree.family_tree_member import FamilyTreeMember
from cogs.utils.checks.is_bot_moderator import is_bot_moderator, is_server_specific_bot_moderator, NotServerSpecific
from cogs.utils.custom_cog import Cog
from cogs.utils.converters import UserID


class ModeratorOnly(Cog):

    def __init__(self, bot:CustomBot):
        super().__init__(self.__class__.__name__)
        self.bot = bot


    async def cog_command_error(self, ctx:Context, error):
        '''
        Local error handler for the cog
        '''

        # Throw errors properly for me
        if ctx.original_author_id in self.bot.owners and not isinstance(error, (CommandOnCooldown, MissingPermissions)):
            text = f'```py\n{error}```'
            await ctx.send(text)
            raise error

        # Missing argument
        if isinstance(error, MissingRequiredArgument):
            await ctx.send("You need to specify a person for this command to work properly.")
            return


        # Argument conversion error
        elif isinstance(error, BadArgument):
            try:
                argument_text = self.bot.bad_argument.search(str(error)).group(2)
                await ctx.send(f"User `{argument_text}` could not be found.")
            except Exception:
                await ctx.send(str(error))
            return

        # Not server specific
        elif isinstance(error, NotServerSpecific):
            await ctx.send(f"You need to be running the server specific version of MarriageBot for this command to work (see `{ctx.clean_prefix}ssf` for more information).")
            return

        # Missing permissions
        elif isinstance(error, MissingRole):
            if ctx.original_author_id in self.bot.owners:
                await ctx.reinvoke()
                return
            await ctx.send(f"You need the `{error.missing_role}` role to run this command.")
            return


    @command(hidden=True)
    @is_bot_moderator()
    async def uncache(self, ctx:Context, user:UserID):
        '''
        Removes a user from the propsal cache.
        '''

        await self.bot.proposal_cache.remove(user)
        await ctx.send("Sent Redis request to remove user from cache.")


    @command(hidden=True)
    @is_bot_moderator()
    async def recache(self, ctx:Context, user:UserID, guild_id:int=0):
        '''Recaches a user's family tree member object'''

        # Read data from DB
        async with self.bot.database() as db:
            parent = await db('SELECT parent_id FROM parents WHERE child_id=$1 AND guild_id=$2', user, guild_id)
            children = await db('SELECT child_id FROM parents WHERE parent_id=$1 AND guild_id=$2', user, guild_id)
            partner = await db('SELECT partner_id FROM marriages WHERE user_id=$1 AND guild_id=$2', user, guild_id)

        # Load data into cache
        children = [i['child_id'] for i in children]
        parent_id = parent[0]['parent_id'] if len(parent) > 0 else None
        partner_id = partner[0]['partner_id'] if len(partner) > 0 else None
        f = FamilyTreeMember(
            user,
            children=children,
            parent_id=parent_id,
            partner_id=partner_id,
            guild_id=guild_id,
        )

        # Push update via redis
        async with self.bot.redis() as re:
            await re.publish_json('TreeMemberUpdate', f.to_json())

        # Output to user
        await ctx.send("Published update.")


    @command(hidden=True)
    @is_bot_moderator()
    async def recachefamily(self, ctx:Context, user:UserID, guild_id:int=0):
        '''Recaches a user's family tree member object, but through their whole family'''

        # Get connections
        db = await self.bot.database.get_connection()
        re = await self.bot.redis.get_connection()

        # Loop through their tree
        family = FamilyTreeMember.get(user, guild_id).span(expand_upwards=True, add_parent=True)[:]
        for i in family:
            parent = await db('SELECT parent_id FROM parents WHERE child_id=$1 AND guild_id=$2', i.id, guild_id)
            children = await db('SELECT child_id FROM parents WHERE parent_id=$1 AND guild_id=$2', i.id, guild_id)
            partner = await db('SELECT partner_id FROM marriages WHERE user_id=$1 AND guild_id=$2', i.id, guild_id)

            # Load data into cache
            children = [i['child_id'] for i in children]
            parent_id = parent[0]['parent_id'] if len(parent) > 0 else None
            partner_id = partner[0]['partner_id'] if len(partner) > 0 else None
            f = FamilyTreeMember(
                i.id,
                children=children,
                parent_id=parent_id,
                partner_id=partner_id,
                guild_id=guild_id,
            )

            # Push update via redis
            await re.publish_json('TreeMemberUpdate', f.to_json())

        # Disconnect from database
        await db.disconnect()
        await re.disconnect()

        # Output to user
        await ctx.send(f"Published `{len(family)}` updates.")


    @command(hidden=True)
    @is_bot_moderator()
    async def loadusers(self, ctx:Context, shard_id:int=None):
        '''
        Loads all families up from the database again
        '''

        async with self.bot.redis() as re:
            await re.publish_json('TriggerStartup', {'shard_id': shard_id})
        await ctx.send(f"Sent trigger to shard {shard_id}.")


    @command(hidden=True)
    @is_server_specific_bot_moderator()
    async def forcemarry(self, ctx:Context, user_a:UserID, user_b:UserID=None):
        '''
        Marries the two specified users
        '''

        if user_b is None:
            user_b = ctx.author.id
        if user_a == user_b:
            await ctx.send("You can't marry yourself (but you can be your own parent ;3).")
            return

        # Get users
        me = FamilyTreeMember.get(user_a, ctx.family_guild_id)
        them = FamilyTreeMember.get(user_b, ctx.family_guild_id)

        # See if they have partners
        if me.partner != None or them.partner != None:
            await ctx.send("One of those users already has a partner.")
            return

        # Update database
        async with self.bot.database() as db:
            try:
                await db.marry(user_a, user_b, ctx.family_guild_id)
            except Exception as e:
                await ctx.send(f"Error encountered: `{e}`")
                return  # Only thrown if two people try to marry at once, so just return
        me._partner = user_b
        them._partner = user_a
        await ctx.send("Consider it done.")


    @command(hidden=True)
    @is_server_specific_bot_moderator()
    async def forcedivorce(self, ctx:Context, user:UserID):
        '''
        Divorces a user from their spouse
        '''

        # Run check
        me = FamilyTreeMember.get(user, ctx.family_guild_id)
        if not me.partner:
            await ctx.send("That person isn't even married .-.")
            return

        # Update database
        async with self.bot.database() as db:
            try:
                await db('DELETE FROM marriages WHERE (user_id=$1 OR partner_id=$1) AND guild_id=$2', user, ctx.family_guild_id)
            except Exception as e:
                await ctx.send(f"Error encountered: `{e}`")
                return  # Honestly this should never be thrown unless the database can't connect
        me.partner._partner = None
        me._partner = None
        await ctx.send("Consider it done.")


    @command(hidden=True)
    @is_server_specific_bot_moderator()
    async def forceadopt(self, ctx:Context, parent:UserID, child:UserID=None):
        '''
        Adds the child to the specified parent
        '''

        if child is None:
            child = parent
            parent = ctx.author.id

        # Run check
        them = FamilyTreeMember.get(child, ctx.family_guild_id)
        child_name = await self.bot.get_name(child)
        if them.parent:
            await ctx.send(f"`{child_name!s}` already has a parent.")
            return

        # Update database
        async with self.bot.database() as db:
            try:
                await db('INSERT INTO parents (parent_id, child_id, guild_id) VALUES ($1, $2, $3)', parent, child, ctx.family_guild_id)
            except Exception as e:
                raise e
                return  # Only thrown when multiple people do at once, just return
        me = FamilyTreeMember.get(parent, ctx.family_guild_id)
        me._children.append(child)
        them._parent = parent
        async with self.bot.redis() as re:
            await re.publish_json('TreeMemberUpdate', me.to_json())
            await re.publish_json('TreeMemberUpdate', them.to_json())
        await ctx.send("Consider it done.")


    @command(aliases=['forceeman'], hidden=True)
    @is_server_specific_bot_moderator()
    async def forceemancipate(self, ctx:Context, user:UserID):
        '''
        Force emancipates a child
        '''

        me = FamilyTreeMember.get(user, ctx.family_guild_id)
        if not me.parent:
            await ctx.send("That user doesn't even have a parent .-.")
            return

        # Update database
        async with self.bot.database() as db:
            try:
                await db('DELETE FROM parents WHERE child_id=$1 AND guild_id=$2', me.id, me._guild_id)
            except Exception as e:
                # await ctx.send(e)
                return  # Should only be thrown when the database can't connect
        me.parent._children.remove(user)
        parent = me.parent
        me._parent = None
        async with self.bot.redis() as re:
            await re.publish_json('TreeMemberUpdate', me.to_json())
            await re.publish_json('TreeMemberUpdate', parent.to_json())
        await ctx.send("Consider it done.")


    @command(hidden=True)
    @is_bot_moderator()
    async def addvoter(self, ctx:Context, user:UserID):
        '''
        Adds a voter to the database
        '''

        self.bot.dbl_votes[user] = dt.now()
        async with self.bot.database() as db:
            try:
                await db('INSERT INTO dbl_votes (user_id, timestamp) VALUES ($1, $2)', user, self.bot.dbl_votes[user])
            except Exception as e:
                await db('UPDATE dbl_votes SET timestamp=$2 WHERE user_id=$1', user, self.bot.dbl_votes[user])
        await ctx.send("Consider it done.")


def setup(bot:CustomBot):
    x = ModeratorOnly(bot)
    bot.add_cog(x)

