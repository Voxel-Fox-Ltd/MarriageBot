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


class Information(object):
    '''
    The information cog
    Handles all marriage/divorce/etc commands
    '''

    def __init__(self, bot:CustomBot):
        self.bot = bot
        self.substitution = compile(r'[^\x00-\x7F\x80-\xFF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF]')


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

        # Setup output variable
        output = ''

        # Get the user's info
        user_info = FamilyTreeMember.get(user.id)
        if len(user_info.children) == 0:
            output += f"`{user!s}` has no children right now."
        else:
            output += f"`{user!s}` has `{len(user_info.children)}` child" + \
            {False:"ren", True:""}.get(len(user_info.children)==1) + ": " + \
            ", ".join([f"`{self.bot.get_user(i.id)!s}` (`{i.id}`)" for i in user_info.children]) + '. '

        # Get their partner's info, if any
        if user_info.partner == None:
            await ctx.send(output)
            return
        user_info = user_info.partner
        user = self.bot.get_user(user_info.id)
        if len(user_info.children) == 0:
            output += f"\nTheir partner, `{user!s}`, has no children right now."
        else:
            output += f"\nTheir partner, `{user!s}`, has `{len(user_info.children)}` child" + \
            {False:"ren", True:""}.get(len(user_info.children)==1) + ": " + \
            ", ".join([f"`{self.bot.get_user(i.id)!s}` (`{i.id}`)" for i in user_info.children]) + '. '

        # Return all output
        await ctx.send(output)

    @command(aliases=['siblings'])
    @cooldown(1, 5, BucketType.user)
    async def sibling(self, ctx:Context, user:User=None):
        '''
        Gives you a list of all of your siblings
        '''

        if user == None:
            user = ctx.author

        # Setup output variable
        output = ''

        # Get the parent's info
        user_info = FamilyTreeMember.get(user.id)
        if user_info.parent == None:
            output += f"`{user!s}` has no parent right now."
        elif len(user_info.parent.children) <= 1:
            output += f"`{user!s}` has no siblings on their side of the family."
        else:
            output += f"`{user!s}` has `{len(user_info.parent.children) - 1}` sibling" + \
            {False:"s", True:""}.get(len(user_info.parent.children)==2) + \
            " from their parent's side: " + \
            ", ".join([f"`{self.bot.get_user(i.id)!s}` (`{i.id}`)" for i in user_info.parent.children if i.id != user.id]) + '. '

        # Get parent's partner's info, if any
        if user_info.parent == None:
            pass
        elif user_info.parent.partner == None:
            pass
        elif len(user_info.parent.partner.children) == 0:
            output += f"\nThey also have no siblings from their parent's partner's side of the family."
        else:
            output += f"\nThey also have `{len(user_info.parent.partner.children)}` sibling" + \
            {False:"s", True:""}.get(len(user_info.parent.partner.children)==1) + \
            " from their parent's partner's side of the family: " + \
            ", ".join([f"`{self.bot.get_user(i.id)!s}` (`{i.id}`)" for i in user_info.parent.partner.children]) + '. '

        # Return all output
        await ctx.send(output)

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


    @command(aliases=['relation'])
    @cooldown(1, 5, BucketType.user)
    async def relationship(self, ctx:Context, user:User, other:User=None):
        '''
        Gets the relationship between the two specified users
        '''

        if user == ctx.author:
            await ctx.send(f"You are you...")
            return

        if other == None:
            user, other = ctx.author, user
        user, other = FamilyTreeMember.get(user.id), FamilyTreeMember.get(other.id)
        relation = user.get_relation(other)
        if relation == None:
            await ctx.send(f"`{user.get_name(self.bot)}` is not related to `{other.get_name(self.bot)}`.")
            return
        await ctx.send(f"`{other.get_name(self.bot)}` is `{user.get_name(self.bot)}`'s {relation}.")


    @command(aliases=['treesize','fs','ts'])
    @cooldown(1, 5, BucketType.user)
    async def familysize(self, ctx:Context, user:User=None):
        '''
        Gives you the size of your family tree
        '''

        if user == None:
            user = ctx.author 
        user = FamilyTreeMember.get(user.id)
        await ctx.send(f"There are `{len(user.span(expand_upwards=True, add_parent=True))}` people in `{user.get_name(self.bot)}`'s family tree.")


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


    @command(aliases=['fulltree', 'ft', 'gt'])
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

        # Write their treemaker code to a file
        # dot_code = tree.to_dot_script(ctx.bot, guild=None if all_guilds else ctx.guild)
        awaitable_dot_code = self.bot.loop.run_in_executor(None, tree.to_dot_script, self.bot, None if all_guilds else ctx.guild)
        try:
            dot_code = await wait_for(awaitable_dot_code, timeout=10.0, loop=self.bot.loop)
        except TimeoutError:
            await ctx.send("Your tree generation has timed out. This is usually due to a loop somewhere in your family tree.")
            return
        with open(f'{self.bot.config["tree_file_location"]}/{ctx.author.id}.dot', 'w', encoding='utf-8') as a:
            a.write(dot_code)

        # Convert to an image
        dot = await create_subprocess_exec(*[
            'dot', 
            '-Tpng', 
            f'{self.bot.config["tree_file_location"]}/{ctx.author.id}.dot', 
            '-o', 
            f'{self.bot.config["tree_file_location"]}/{ctx.author.id}.png', 
            '-Gcharset=UTF-8', 
            '-Gsize=200\\!', 
            '-Gdpi=100'
            ], loop=self.bot.loop
        )
        await wait_for(dot.wait(), 10.0, loop=self.bot.loop)
        try:
            dot.kill()
        except Exception: 
            pass

        # Send file and delete cached
        try:
            file = File(fp=f'{self.bot.config["tree_file_location"]}/{ctx.author.id}.png')
            text = f"{ctx.author.mention}, you can update how your tree looks with `{ctx.prefix}help customise` c:"
            await ctx.send(text, file=file)
        except Exception:
            return 
        return


def setup(bot:CustomBot):
    x = Information(bot)
    bot.add_cog(x)
