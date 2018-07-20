from traceback import format_exc
from asyncio import iscoroutine
from discord import Member
from discord.ext.commands import command, Context
from cogs.utils.custom_bot import CustomBot
from cogs.utils.family_tree.family_tree_member import FamilyTreeMember


class CalebOnly(object):
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
    async def addallusers(self, ctx:Context):
        '''
        Adds all users to the family tree holder
        '''

        await ctx.send('Adding now...')
        async with self.bot.database() as db:
            partnerships = await db('SELECT * FROM marriages WHERE valid=TRUE')
            parents = await db('SELECT * FROM parents')
        for i in partnerships:
            FamilyTreeMember(discord_id=i['user_id'], children=[], parent_id=None, partner_id=i['partner_id'])
        for i in parents:
            parent = FamilyTreeMember.get(i['parent_id'])
            parent.children.append(i['child_id'])
            child = FamilyTreeMember.get(i['child_id'])
            child.parent = i['parent_id']
        await ctx.send('Done.')


    @command(hidden=True)
    async def ev(self, ctx:Context, *, content:str):
        '''
        Runs some text through Python's eval function
        '''

        try:
            ans = eval(content, globals(), locals())
        except Exception as e:
            await ctx.send('```py\n' + format_exc() + '```')
            return
        if iscoroutine(ans):
            ans = await ans
        await ctx.send('```py\n' + str(ans) + '```')


    @command(aliases=['rld'])
    async def reload(self, ctx:Context, *cog_name:str):
        '''
        Unloads a cog from the bot
        '''

        self.bot.unload_extension('cogs.' + '_'.join([i for i in cog_name]))
        try:
            self.bot.load_extension('cogs.' + '_'.join([i for i in cog_name]))
        except Exception as e:
            await ctx.send('```py\n' + format_exc() + '```')
            return
        await ctx.send('Cog reloaded.')
        


def setup(bot:CustomBot):
    x = CalebOnly(bot)
    bot.add_cog(x)


