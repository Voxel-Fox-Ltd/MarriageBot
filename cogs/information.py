from discord import Member
from discord.ext.commands import command, Context
from cogs.utils.custom_bot import CustomBot


class Information(object):
    '''
    The information cog
    Handles all marriage/divorce/etc commands
    '''

    def __init__(self, bot:CustomBot):
        self.bot = bot


    @command(aliases=['spouse', 'husband', 'wife'])
    async def partner(self, ctx:Context, user:Member=None):
        '''
        Shows you the partner of a given user
        '''

        if not user:
            user = ctx.author

        async with self.bot.database() as db:
            x = await db.get_marriage(user)
        if not x:
            await ctx.send(f"`{user!s}` is not currently married.")
            return
        i = x[0]

        u1 = self.bot.get_user(i['user_id'])
        u2 = self.bot.get_user(i['partner_id'])
        await ctx.send(f"`{u1!s}` is currently married to `{u2!s}`.")


    @command(aliases=['child'])
    async def children(self, ctx:Context, user:Member=None):
        '''
        Gives you a list of all of your children
        '''

        if user == None:
            user = ctx.author

        async with self.bot.database() as db:
            x = await db('SELECT * FROM parents WHERE parent_id=$1', user.id)
        if not x:
            await ctx.send(f"`{user!s}` has no children right now.")
            return
        await ctx.send(f"`{user!s}` has `{len(x)}` child" + {False:"ren",True:""}.get(len(x)==1) + ": " + ", ".join([f"`{self.bot.get_user(i['child_id'])!s}`" for i in x]))

    @command()
    async def parent(self, ctx:Context, user:Member=None):
        '''
        Gives you a list of all of your children
        '''

        if user == None:
            user = ctx.author

        async with self.bot.database() as db:
            x = await db('SELECT * FROM parents WHERE child_id=$1', user.id)
        if not x:
            await ctx.send(f"`{user!s}` has no parent.")
            return
        await ctx.send(f"`{user!s}`'s parent is `{self.bot.get_user(x[0]['parent_id'])!s}`.")


def setup(bot:CustomBot):
    x = Information(bot)
    bot.add_cog(x)
