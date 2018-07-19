from traceback import format_exc
from asyncio import iscoroutine
from discord import Member
from discord.ext.commands import command, Context
from cogs.utils.custom_bot import CustomBot
from cogs.utils.family_tree.family_tree import FamilyTree


class Parentage(object):
    '''
    The parentage cog
    Handles the adoption of parents
    '''

    def __init__(self, bot:CustomBot):
        self.bot = bot
        self.last_tree = None


    async def __local_check(self, ctx:Context):
        return str(ctx.author) == 'Caleb#2831'


    @command(hidden=True)
    async def tree(self, ctx:Context, root:Member, depth:int=3):
        '''
        '''

        ft = FamilyTree(root.id, depth)
        async with self.bot.database() as db:
            await ft.populate_tree(db)
        self.last_tree = ft 
        await ctx.send('Done.')


    @command(hidden=True)
    async def ev(self, ctx:Context, *, content:str):
        '''
        Runs some text through Python's eval function
        '''

        try:
            ans = eval(content)
        except Exception as e:
            await ctx.send('```py\n' + format_exc() + '```')
            return
        if iscoroutine(ans):
            ans = await ans
        await ctx.send('```py\n' + str(ans) + '```')
        


def setup(bot:CustomBot):
    x = Parentage(bot)
    bot.add_cog(x)


