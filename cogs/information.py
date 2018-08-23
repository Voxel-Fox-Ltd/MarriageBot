from random import choice
from string import ascii_lowercase
from os import remove
from re import compile
from io import BytesIO
from asyncio import sleep, create_subprocess_exec, wait_for
from discord import Member, File, User
from discord.ext.commands import command, Context
from cogs.utils.custom_bot import CustomBot
from cogs.utils.checks.can_send_files import can_send_files
from cogs.utils.family_tree.family_tree_member import FamilyTreeMember
from cogs.utils.family_tree.familytreemaker import generate_dot_file


get_random_string = lambda: ''.join(choice(ascii_lowercase) for i in range(6))


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

        # Get the user's info
        user_info = FamilyTreeMember.get(user.id)
        if user_info.partner == None:
            await ctx.send(f"`{user!s}` is not currently married.")
            return

        partner = self.bot.get_user(user_info.partner)
        await ctx.send(f"`{user!s}` is currently married to `{partner!s}`.")


    @command(aliases=['child'])
    async def children(self, ctx:Context, user:Member=None):
        '''
        Gives you a list of all of your children
        '''

        if user == None:
            user = ctx.author

        # Get the user's info
        user_info = FamilyTreeMember.get(user.id)
        if len(user_info.children) == 0:
            await ctx.send(f"`{user!s}` has no children right now.")
            return
        await ctx.send(
            f"`{user!s}` has `{len(user_info.children)}` child" + 
            {False:"ren",True:""}.get(len(user_info.children)==1) + ": " + 
            ", ".join([f"`{self.bot.get_user(i)!s}`" for i in user_info.children])
            )

    @command()
    async def parent(self, ctx:Context, user:Member=None):
        '''
        Tells you who your parent is
        '''

        if user == None:
            user = ctx.author

        user_info = FamilyTreeMember.get(user.id)
        if user_info.parent == None:
            await ctx.send(f"`{user!s}` has no parent.")
            return
        await ctx.send(f"`{user!s}`'s parent is `{self.bot.get_user(user_info.parent)!s}`.")


    @command()
    @can_send_files()
    async def treefile(self, ctx:Context, root:Member=None):
        '''
        Gives you the full family tree of a user
        '''

        if root == None:
            root = ctx.author

        text = FamilyTreeMember.get(root.id).generate_gedcom_file(self.bot)
        file = BytesIO(text.encode())
        await ctx.send(file=File(file, filename=f'Tree of {root.id}.ged'))


    @command(aliases=['familytree'])
    @can_send_files()
    async def tree(self, ctx:Context, root:Member=None, depth:int=-1):
        '''
        Gets the family tree of a given user
        '''

        try:
            return await self.treemaker(ctx, root, depth, False)
        except Exception as e:
            await ctx.send("I encountered an error while trying to generate your family tree. Could you inform `Caleb#2831`, so he can fix this in future for you?")
            raise e


    @command(aliases=['fulltree'])
    @can_send_files()
    async def globaltree(self, ctx:Context, root:User=None, depth:int=-1):
        '''
        Gets the global family tree of a given user
        '''

        try:
            return await self.treemaker(ctx, root, depth, True)
        except Exception as e:
            await ctx.send("I encountered an error while trying to generate your family tree. Could you inform `Caleb#2831`, so he can fix this in future for you?")
            raise e


    async def treemaker(self, ctx:Context, root:User, depth:int, all_guilds:bool):

        # if str(ctx.author) != 'Caleb#2831': 
        #     return await ctx.send("This command is temporarily disabled. Apologies.")

        if root == None:
            root = ctx.author
        if depth <= 0:
            depth = -1
        root_user = root

        # Get their family tree
        await ctx.trigger_typing()
        tree = FamilyTreeMember.get(root.id)

        # Make sure they have one
        if tree.children == [] and tree.partner == None and tree.parent == None:
            await ctx.send(f"`{root_user!s}` has no family to put into a tree .-.")
            return

        # Start the 3-step conversion process
        root, text = tree.to_tree_string(ctx, expand_backwards=depth, depth=depth*2, all_guilds=all_guilds)
        if text == '':
            await ctx.send(f"`{root_user!s}` has no family to put into a tree .-.")
            return

        # Make the random string that stops things messing up
        random_string = get_random_string()

        # Write their treemaker code to a file
        with open(f'./trees/{random_string}_{root.id}.txt', 'w', encoding='utf-8') as a:
            a.write(text)

        # Convert and write to a dot file
        f = open(f'./trees/{random_string}_{root.id}.dot', 'w')
        treemaker = await create_subprocess_exec(*[
            'python3.6', 
            './cogs/utils/family_tree/familytreemaker.py', 
            f'./trees/{random_string}_{root.id}.txt'
            ], stdout=f, loop=self.bot.loop)
        # await treemaker.wait()
        await wait_for(treemaker.wait(), 10.0, loop=self.bot.loop)
        try:
            treemaker.kill()
        except Exception as e: 
            pass
        f.close()

        # Convert to an image
        dot = await create_subprocess_exec(*[
            'dot', 
            '-Tpng', 
            f'./trees/{random_string}_{root.id}.dot', 
            '-o', 
            f'./trees/{random_string}_{root.id}.png', 
            '-Gcharset=UTF-8', 
            '-Gsize=200\\!', 
            '-Gdpi=100'
            ], loop=self.bot.loop)
        # await dot.wait()
        await wait_for(dot.wait(), 10.0, loop=self.bot.loop)
        try:
            dot.kill()
        except Exception as e: 
            pass

        # Send file and delete cached
        try:
            await ctx.send(ctx.author.mention, file=File(fp=f'./trees/{random_string}_{root.id}.png'))
        except Exception as e:
            return 
        return
        # await sleep(5)  # Just so the file still isn't sending
        # for i in [f'./trees/{random_string}_{root.id}.txt', f'./trees/{random_string}_{root.id}.dot', f'./trees/{random_string}_{root.id}.png']:
        #     # _ = await self.bot.loop.run_in_executor(None, remove, i)
        #     # await create_subprocess_exec('rm', i, loop=self.bot.loop)
        #     pass


def setup(bot:CustomBot):
    x = Information(bot)
    bot.add_cog(x)
