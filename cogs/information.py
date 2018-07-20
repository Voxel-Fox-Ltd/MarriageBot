from subprocess import run
from os import remove
from re import compile
from asyncio import sleep
from discord import Member, File
from discord.ext.commands import command, Context
from cogs.utils.custom_bot import CustomBot
from cogs.utils.family_tree.family_tree import FamilyTree


class Information(object):
    '''
    The information cog
    Handles all marriage/divorce/etc commands
    '''

    def __init__(self, bot:CustomBot):
        self.bot = bot
        self.substitution = compile(r'[^\x00-\x7F\x80-\xFF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF]')


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
        Tells you who your parent is
        '''

        if user == None:
            user = ctx.author

        async with self.bot.database() as db:
            x = await db('SELECT * FROM parents WHERE child_id=$1', user.id)
        if not x:
            await ctx.send(f"`{user!s}` has no parent.")
            return
        await ctx.send(f"`{user!s}`'s parent is `{self.bot.get_user(x[0]['parent_id'])!s}`.")


    @command()
    async def tree(self, ctx:Context, root:Member=None, depth:int=3):
        '''
        Gets the family tree of a given user
        '''

        if root == None:
            root = ctx.author
        if depth >= 8:
            depth = 8

        # Get their family tree
        await ctx.trigger_typing()
        ft = FamilyTree(root.id, depth, root.id)
        async with self.bot.database() as db:
            await ft.populate_tree(db)

        # Make sure they have one
        if ft.root.children == [] and ft.root.partner == None and ft.root.parent == None:
            await ctx.send(f"{root!s} has no family to put into a tree .-.")
            return

        # Expand upwards
        x = ft.root
        while True:
            if x.parent == None:
                break
            else:
                x = x.parent
                depth += 1
        ft = FamilyTree(x.id, depth, root.id)
        async with self.bot.database() as db:
            await ft.populate_tree(db)

        # Start the 3-step conversion process
        with open(f'./trees/{x.id}.txt', 'w', encoding='utf-8') as a:
            text = ft.stringify(self.bot)
            a.write(self.substitution.sub('', text))
        f = open(f'./trees/{x.id}.dot', 'w')
        _ = run(['py', './cogs/utils/family_tree/familytreemaker.py', '-a', self.substitution.sub('', str(x.get_name(self.bot))), f'./trees/{x.id}.txt'], stdout=f)
        f.close()
        _ = run(['dot', '-Tpng', f'./trees/{x.id}.dot', '-o', f'./trees/{x.id}.png', '-Gcharset=latin1', '-Gsize=200\\!', '-Gdpi=100'])

        # Send file and delete cached
        await ctx.send(file=File(fp=f'./trees/{x.id}.png'))
        await sleep(1)  # Just so the file still isn't sending
        for i in [f'./trees/{x.id}.txt', f'./trees/{x.id}.dot', f'./trees/{x.id}.png']:
            _ = remove(i)


def setup(bot:CustomBot):
    x = Information(bot)
    bot.add_cog(x)
