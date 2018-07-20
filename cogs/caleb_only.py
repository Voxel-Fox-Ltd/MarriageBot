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


    # @command()
    # async def related(self, ctx:Context, child:Member, parent:Member):
    #     await ctx.trigger_typing()
    #     async with self.bot.database() as db:
    #         family_tree1 = FamilyTree(child.id, 6, go_back=-1)  # Get the instigator's tree
    #         await family_tree1.populate_tree(db)
    #         family_tree2 = FamilyTree(parent.id, 6, go_back=-1)  # Get the instigator's tree
    #         await family_tree2.populate_tree(db)
        
    #     # If they are, tell them off
    #     treeset_1 = set([i.id for i in family_tree1.all_users()])
    #     treeset_2 = set([i.id for i in family_tree2.all_users()])
    #     if treeset_1.intersection(treeset_2):
    #         await ctx.send('Yes')
    #         return
    #     await ctx.send('No')
        


def setup(bot:CustomBot):
    x = CalebOnly(bot)
    bot.add_cog(x)


