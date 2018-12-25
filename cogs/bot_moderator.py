from discord import User
from discord.ext.commands import command, Context, cooldown
from discord.ext.commands.cooldowns import BucketType

from cogs.utils.custom_bot import CustomBot
from cogs.utils.family_tree.family_tree_member import FamilyTreeMember


class ModeratorOnly(object):

    def __init__(self, bot:CustomBot):
        self.bot = bot 


    def __local_check(self, ctx:Context):
        if ctx.author.id in self.bot.config['owners']:
            return True
        elif ctx.guild == None:
            return False
        if self.bot.config['bot_admin_role'] in [i.id for i in ctx.author.roles]:
            return True
        return False


    @command()
    async def uncache(self, ctx:Context, user:User):
        '''
        Removes a user from the propsal cache.
        '''

        x = self.bot.proposal_cache.remove(user.id)
        if x:
            await ctx.send("Removed from proposal cache.")
        else:
            await ctx.send("The user wasn't even in the cache but go off I guess.")


    @command()
    async def forcemarry(self, ctx:Context, user_a:User, user_b:User):
        '''
        Marries the two specified users
        '''

        async with self.bot.database() as db:
            try:
                await db.marry(user_a, user_b)
            except Exception as e:
                return  # Only thrown if two people try to marry at once, so just return
        me = FamilyTreeMember.get(user_a.id)
        me._partner = user_b.id 
        them = FamilyTreeMember.get(user_b.id)
        them._partner = user_a.id
        await ctx.send("Consider it done.")


    @command()
    async def forcedivorce(self, ctx:Context, user:User):
        '''
        Divorces a user from their spouse
        '''

        async with self.bot.database() as db:
            try:
                await db('DELETE FROM marriages WHERE user_id=$1 OR partner_id=$1', user.id)
            except Exception as e:
                return  # Honestly this should never be thrown unless the database can't connect
        me = FamilyTreeMember.get(user.id)
        if not me.partner:
            await ctx.send("That person isn't even married .-.")
            return
        me.partner._partner = None 
        me._partner = None
        await ctx.send("Consider it done.")


    @command()
    async def forceadopt(self, ctx:Context, parent:User, child:User):
        '''
        Adds the child to the specified parent
        '''

        async with self.bot.database() as db:
            try:
                await db('INSERT INTO parents (parent_id, child_id) VALUES ($1, $2)', parent.id, child.id)
            except Exception as e:
                return  # Only thrown when multiple people do at once, just return
        me = FamilyTreeMember.get(parent.id)
        me._children.append(child.id)
        them = FamilyTreeMember.get(child.id)
        them._parent = parent.id
        await ctx.send("Consider it done.")


    @command(aliases=['forceeman'])
    async def forceemancipate(self, ctx:Context, user:User):
        '''
        Force emancipates a child
        '''

        async with self.bot.database() as db:
            try:
                await db('DELETE FROM parents WHERE child_id=$1', user.id)
            except Exception as e:
                return  # Should only be thrown when the database can't connect
        me = FamilyTreeMember.get(user.id)
        if not user.parent:
            await ctx.send("That user doesn't even have a parent .-.")
            return 
        me.parent._children.remove(user.id)
        me._parent = None
        await ctx.send("Consider it done.")


def setup(bot:CustomBot):
    x = ModeratorOnly(bot)
    bot.add_cog(x)
    
