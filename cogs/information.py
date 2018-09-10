from random import choice
from string import ascii_lowercase
from os import remove
from re import compile
from io import BytesIO
from asyncio import sleep, create_subprocess_exec, wait_for
from discord import Member, File, User
from discord.ext.commands import command, Context, cooldown
from discord.ext.commands.cooldowns import BucketType
from cogs.utils.custom_bot import CustomBot
from cogs.utils.checks.can_send_files import can_send_files
from cogs.utils.family_tree.family_tree_member import FamilyTreeMember
from cogs.utils.family_tree.family import Family


get_random_string = lambda: ''.join(choice(ascii_lowercase) for i in range(6))


class Information(object):
    '''
    The information cog
    Handles all marriage/divorce/etc commands
    '''

    def __init__(self, bot:CustomBot):
        self.bot = bot
        self.substitution = compile(r'[^\x00-\x7F\x80-\xFF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF]')
        self.fam = None


    @command(aliases=['spouse', 'husband', 'wife'])
    @cooldown(1, 5, BucketType.user)
    async def partner(self, ctx:Context, user:User=None):
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

        partner = self.bot.get_user(user_info.partner.id)
        await ctx.send(f"`{user!s}` is currently married to `{partner!s}` (`{partner.id}`).")


    @command(aliases=['child'])
    @cooldown(1, 5, BucketType.user)
    async def children(self, ctx:Context, user:User=None):
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
            ", ".join([f"`{self.bot.get_user(i.id)!s}` (`{i.id}`)" for i in user_info.children])
        )

    @command()
    @cooldown(1, 5, BucketType.user)
    async def parent(self, ctx:Context, user:User=None):
        '''
        Tells you who your parent is
        '''

        if user == None:
            user = ctx.author

        user_info = FamilyTreeMember.get(user.id)
        if user_info.parent == None:
            await ctx.send(f"`{user!s}` has no parent.")
            return
        await ctx.send(f"`{user!s}`'s parent is `{self.bot.get_user(user_info.parent.id)!s}` (`{user_info.parent.id}`).")


    @command()
    @can_send_files()
    @cooldown(1, 5, BucketType.user)
    async def treefile(self, ctx:Context, root:Member=None):
        '''
        Gives you the full family tree of a user
        '''

        if root == None:
            root = ctx.author

        text = FamilyTreeMember.get(root.id).generate_gedcom_script(self.bot)
        file = BytesIO(text.encode())
        await ctx.send(file=File(file, filename=f'Tree of {root.id}.ged'))


    @command(aliases=['familytree'])
    @can_send_files()
    @cooldown(1, 5, BucketType.user)
    async def tree(self, ctx:Context, root:Member=None):
        '''
        Gets the family tree of a given user
        '''

        if ctx.guild == None:
            await ctx.send("This command cannot be used in private messages. Please use the `fulltree` command in its place.")
            return

        try:
            return await self.treemaker(ctx, root, False)
        except Exception as e:
            # await ctx.send("I encountered an error while trying to generate your family tree. Could you inform `Caleb#2831`, so he can fix this in future for you?")
            raise e


    @command(aliases=['fulltree'])
    @can_send_files()
    @cooldown(1, 5, BucketType.user)
    async def globaltree(self, ctx:Context, root:User=None):
        '''
        Gets the global family tree of a given user
        '''

        try:
            return await self.treemaker(ctx, root, True)
        except Exception as e:
            # await ctx.send("I encountered an error while trying to generate your family tree. Could you inform `Caleb#2831`, so he can fix this in future for you?")
            raise e


    async def treemaker(self, ctx:Context, root:User, all_guilds:bool):

        # if ctx.author.id not in self.bot.config['owners']: 
        #     return await ctx.send("This command is temporarily disabled. Apologies.")

        if root == None:
            root = ctx.author
        root_user = root

        # Get their family tree
        await ctx.trigger_typing()
        tree = FamilyTreeMember.get(root_user.id)

        # Make sure they have one
        if tree.is_empty:
            await ctx.send(f"`{root_user!s}` has no family to put into a tree .-.")
            return

        # Make the random string that stops things messing up
        random_string = get_random_string()

        # Write their treemaker code to a file
        with open(f'./trees/{random_string}_{root_user.id}.dot', 'w', encoding='utf-8') as a:
            a.write(Family.get_full_tree(ctx, tree, all_guilds=all_guilds))

        # Convert to an image
        dot = await create_subprocess_exec(*[
            'dot', 
            '-Tpng', 
            f'./trees/{random_string}_{root_user.id}.dot', 
            '-o', 
            f'./trees/{random_string}_{root_user.id}.png', 
            '-Gcharset=UTF-8', 
            '-Gsize=200\\!', 
            '-Gdpi=100'
            ], loop=self.bot.loop
        )
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
