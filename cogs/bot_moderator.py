from datetime import datetime as dt
from typing import Union

from discord import User
from discord.ext.commands import command, Context, cooldown
from discord.ext.commands import MissingPermissions, MissingRequiredArgument, BadArgument, CommandOnCooldown
from discord.ext.commands.cooldowns import BucketType

from cogs.utils.custom_bot import CustomBot
from cogs.utils.family_tree.family_tree_member import FamilyTreeMember
from cogs.utils.checks.is_bot_moderator import is_bot_moderator
from cogs.utils.custom_cog import Cog


class ModeratorOnly(Cog):

    def __init__(self, bot:CustomBot):
        super().__init__(self.__class__.__name__)
        self.bot = bot 


    async def cog_command_error(self, ctx:Context, error):
        '''
        Local error handler for the cog
        '''

        # Throw errors properly for me
        if ctx.author.id in self.bot.config['owners'] and not isinstance(error, CommandOnCooldown):
            text = f'```py\n{error}```'
            await ctx.send(text)
            raise error

        # Missing argument
        if isinstance(error, MissingRequiredArgument):
            await ctx.send("You need to specify a person for this command to work properly.")
            return

    
        # Argument conversion error
        elif isinstance(error, BadArgument):
            argument_text = self.bot.bad_argument.search(str(error)).group(2)
            await ctx.send(f"User `{argument_text}` could not be found.")
            return

        # Missing permissions
        elif isinstance(error, MissingPermissions):
            await ctx.send(f"You need the `{error.missing_perms[0]}` permission to run this command.")
            return


    @command(hidden=True)
    @is_bot_moderator()
    async def uncache(self, ctx:Context, user:Union[User, int]):
        '''
        Removes a user from the propsal cache.
        '''

        if isinstance(user, User):
            user_id = user.id
        else:
            user_id = user 
        await self.bot.proposal_cache.remove(user_id)
        await ctx.send("Sent Redis request to remove user from cache.")


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
    @is_bot_moderator()
    async def forcemarry(self, ctx:Context, user_a:User, user_b:User):
        '''
        Marries the two specified users
        '''

        # Get users
        me = FamilyTreeMember.get(user_a.id, ctx.guild.id if ctx.guild.id in self.bot.server_specific_families else 0)
        them = FamilyTreeMember.get(user_b.id, ctx.guild.id if ctx.guild.id in self.bot.server_specific_families else 0)

        # See if they have partners
        if me.partner != None or them.partner != None:
            await ctx.send("One of those users already has a partner.")
            return

        # Update database
        async with self.bot.database() as db:
            try:
                await db.marry(user_a, user_b, ctx.guild.id if ctx.guild.id in self.bot.server_specific_families else 0)
            except Exception as e:
                await ctx.send(f"Error encountered: `{e}`")
                return  # Only thrown if two people try to marry at once, so just return
        me._partner = user_b.id 
        them._partner = user_a.id
        await ctx.send("Consider it done.")


    @command(hidden=True)
    @is_bot_moderator()
    async def forcedivorce(self, ctx:Context, user:User):
        '''
        Divorces a user from their spouse
        '''

        # Run check
        me = FamilyTreeMember.get(user.id, ctx.guild.id if ctx.guild.id in self.bot.server_specific_families else 0)
        if not me.partner:
            await ctx.send("That person isn't even married .-.")
            return

        # Update database
        async with self.bot.database() as db:
            try:
                await db('DELETE FROM marriages WHERE (user_id=$1 OR partner_id=$1) AND guild_id=$2', user.id, ctx.guild.id if ctx.guild.id in self.bot.server_specific_families else 0)
            except Exception as e:
                await ctx.send(f"Error encountered: `{e}`")
                return  # Honestly this should never be thrown unless the database can't connect
        me.partner._partner = None 
        me._partner = None
        await ctx.send("Consider it done.")


    @command(hidden=True)
    @is_bot_moderator()
    async def forceadopt(self, ctx:Context, parent:User, child:User):
        '''
        Adds the child to the specified parent
        '''

        # Run check
        them = FamilyTreeMember.get(child.id, ctx.guild.id if ctx.guild.id in self.bot.server_specific_families else 0)
        if them.parent:
            await ctx.send("`{child!s}` already has a parent.")
            return

        # Update database
        async with self.bot.database() as db:
            try:
                await db('INSERT INTO parents (parent_id, child_id, guild_id) VALUES ($1, $2, $3)', parent.id, child.id, ctx.guild.id if ctx.guild.id in self.bot.server_specific_families else 0)
            except Exception as e:
                return  # Only thrown when multiple people do at once, just return
        me = FamilyTreeMember.get(parent.id, ctx.guild.id if ctx.guild.id in self.bot.server_specific_families else 0)
        me._children.append(child.id)
        them._parent = parent.id
        await ctx.send("Consider it done.")


    @command(aliases=['forceeman'], hidden=True)
    @is_bot_moderator()
    async def forceemancipate(self, ctx:Context, user:Union[User, int]):
        '''
        Force emancipates a child
        '''

        # Run check
        if isinstance(user, User):
            user_id = user.id
        else:
            user_id = user 
        me = FamilyTreeMember.get(user_id, ctx.guild.id if ctx.guild.id in self.bot.server_specific_families else 0)
        if not me.parent:
            await ctx.send("That user doesn't even have a parent .-.")
            return

        # Update database
        async with self.bot.database() as db:
            try:
                await db('DELETE FROM parents WHERE child_id=$1 AND guild_id=$2', user_id, ctx.guild.id if ctx.guild.id in self.bot.server_specific_families else 0)
            except Exception as e:
                return  # Should only be thrown when the database can't connect 
        me.parent._children.remove(user_id)
        me._parent = None
        async with self.bot.redis() as re:
            await re.publish_json('TreeMemberUpdate', me.to_json())
            await re.publish_json('TreeMemberUpdate', me.parent.to_json())
        await ctx.send("Consider it done.")


    @command(hidden=True)
    @is_bot_moderator()
    async def addvoter(self, ctx:Context, user:User):
        '''
        Adds a voter to the database
        '''

        self.bot.dbl_votes[user.id] = dt.now()
        async with self.bot.database() as db:
            try:
                await db('INSERT INTO dbl_votes (user_id, timestamp) VALUES ($1, $2)', user.id, self.bot.dbl_votes[user.id])
            except Exception as e:
                await db('UPDATE dbl_votes SET timestamp=$2 WHERE user_id=$1', user.id, self.bot.dbl_votes[user.id])
        await ctx.send("Consider it done.")


def setup(bot:CustomBot):
    x = ModeratorOnly(bot)
    bot.add_cog(x)
    
