from random import choice
from os import remove
from re import compile
from io import BytesIO
from asyncio import sleep, create_subprocess_exec, wait_for, TimeoutError as AsyncTimeoutError

from discord import Member, File, User
from discord.ext.commands import command, Context, cooldown
from discord.ext.commands import CommandOnCooldown, MissingRequiredArgument, BadArgument, DisabledCommand
from discord.ext.commands.cooldowns import BucketType

from cogs.utils.custom_bot import CustomBot
from cogs.utils.checks.can_send_files import can_send_files
from cogs.utils.checks.is_voter import is_voter_predicate, is_voter, IsNotVoter
from cogs.utils.checks.is_donator import is_patreon, IsNotDonator
from cogs.utils.checks.no_tree_cache import no_tree_cache, IsTreeCached
from cogs.utils.family_tree.family_tree_member import FamilyTreeMember
from cogs.utils.customised_tree_user import CustomisedTreeUser
from cogs.utils.custom_cog import Cog
from cogs.utils.checks.bot_is_ready import bot_is_ready, BotNotReady


class Information(Cog):
    '''
    The information cog
    Handles all marriage/divorce/etc commands
    '''

    VOTER_TREE_COOLDOWN_TIME = 30.0  # Seconds
    DONATOR_TREE_COOLDOWN_TIME = 10.0

    def __init__(self, bot:CustomBot):
        super().__init__(self.__class__.__name__)
        self.bot = bot
        self.substitution = compile(r'[^\x00-\x7F\x80-\xFF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF]')


    async def cog_command_error(self, ctx:Context, error):
        '''
        Local error handler for the cog
        '''

        # Throw errors properly for me
        if ctx.author.id in self.bot.config['owners'] and not isinstance(error, (CommandOnCooldown, DisabledCommand, IsNotVoter, IsNotDonator, IsTreeCached)):
            text = f'```py\n{error}```'
            await ctx.send(text)
            raise error

        # Missing argument
        if isinstance(error, MissingRequiredArgument):
            await ctx.send("You need to specify a person for this command to work properly.")
            return

        # Tree cache
        elif isinstance(error, IsTreeCached):
            if ctx.author.id in self.bot.config['owners']:
                await ctx.reinvoke()
            else:
                await ctx.send("Please wait for your other tree to be generated first.")
            return

        # Cooldown
        elif isinstance(error, CommandOnCooldown):
            # Bypass for owner
            if ctx.author.id in self.bot.config['owners']:
                await ctx.reinvoke()
            # Possible bypass for voter
            elif ctx.command.name in ['tree', 'globaltree']:
                if is_voter_predicate(ctx) and error.retry_after <= (error.cooldown.per - self.VOTER_TREE_COOLDOWN_TIME):
                    ctx.command.reset_cooldown(ctx)
                    await ctx.invoke(ctx.command, *ctx.args, **ctx.kwargs)
                elif is_voter_predicate(ctx) and error.retry_after > (error.cooldown.per - self.VOTER_TREE_COOLDOWN_TIME):
                    await ctx.send(f"You can only use this command once every `{error.cooldown.per:.0f} seconds` (or once every `{self.VOTER_TREE_COOLDOWN_TIME} seconds`, for you, since you're a voter) per server. You may use this again in `{(error.retry_after - (error.cooldown.per - self.VOTER_TREE_COOLDOWN_TIME)):.2f} seconds`.")
                else:
                    await ctx.send(f"You can only use this command once every `{error.cooldown.per:.0f} seconds` (or once every `{self.VOTER_TREE_COOLDOWN_TIME} seconds`, if you `m!vote`) per server. You may use this again in `{error.retry_after:.2f} seconds`.")
                    # await ctx.send(f"You can only use this command once every `{error.cooldown.per:.0f} seconds` per server. You may use this again in `{error.retry_after:.2f} seconds`.")
            
            # Default output
            else:
                await ctx.send(f"You can only use this command once every `{error.cooldown.per:.0f} seconds` per server. You may use this again in `{error.retry_after:.2f} seconds`.")
            return

        # Voter
        elif isinstance(error, IsNotVoter):
            # Bypass for owner
            if ctx.author.id in self.bot.config['owners']:
                await ctx.reinvoke()
            else:
                await ctx.send(f"You need to vote on DBL (`{ctx.prefix}vote`) to be able to run this command.")
            return

        # Donator
        elif isinstance(error, IsNotDonator):
            # Bypass for owner
            if ctx.author.id in self.bot.config['owners']:
                await ctx.reinvoke()
            else:
                await ctx.send(f"You need to be a Patreon subscriber (`{ctx.prefix}donate`) to be able to run this command.")
            return
    
        # Argument conversion error
        elif isinstance(error, BadArgument):
            argument_text = self.bot.bad_argument.search(str(error)).group(2)
            await ctx.send(f"User `{argument_text}` could not be found.")
            return

        # Disabled command
        elif isinstance(error, DisabledCommand):
            if ctx.author.id in self.bot.config['owners']:
                await ctx.reinvoke()
            else:
                await ctx.send("This command has been temporarily disabled. Apologies for any inconvenience.")
            return

        # Bot ready
        elif isinstance(error, BotNotReady):
            await ctx.send("The bot isn't ready to start processing that command yet - please wait.")
            return


    @command(aliases=['spouse', 'husband', 'wife', 'marriage'])
    @bot_is_ready()
    @cooldown(1, 5, BucketType.user)
    async def partner(self, ctx:Context, user:User=None):
        '''
        Shows you the partner of a given user
        '''

        if not user:
            user = ctx.author

        # Get the user's info
        user_info = FamilyTreeMember.get(user.id, self.bot.get_tree_guild_id(ctx.guild.id))
        if user_info._partner == None:
            await ctx.send(f"`{user!s}` is not currently married.")
            return

        partner_name = await self.bot.get_name(user_info._partner)
        await ctx.send(f"`{user!s}` is currently married to `{partner_name}` (`{user_info._partner}`).")


    @command(aliases=['child', 'kids'])
    @bot_is_ready()
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
        user_info = FamilyTreeMember.get(user.id, self.bot.get_tree_guild_id(ctx.guild.id))
        if len(user_info._children) == 0:
            output += f"`{user!s}` has no children right now."
        else:
            output += f"`{user!s}` has `{len(user_info._children)}` child" + \
            {False:"ren", True:""}.get(len(user_info._children)==1) + ": " + \
            ", ".join([f"`{self.bot.get_user(i)!s}` (`{i}`)" for i in user_info._children]) + '. '

        # Get their partner's info, if any
        if user_info._partner == None:
            await ctx.send(output)
            return
        user_info = user_info.partner
        user = self.bot.get_user(user_info.id)
        if len(user_info._children) == 0:
            output += f"\nTheir partner, `{user!s}`, has no children right now."
        else:
            output += f"\nTheir partner, `{user!s}`, has `{len(user_info._children)}` child" + \
            {False:"ren", True:""}.get(len(user_info._children)==1) + ": " + \
            ", ".join([f"`{self.bot.get_user(i)!s}` (`{i}`)" for i in user_info._children]) + '. '

        # Return all output
        await ctx.send(output)

    @command(aliases=['siblings'])
    @bot_is_ready()
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
        user_info = FamilyTreeMember.get(user.id, self.bot.get_tree_guild_id(ctx.guild.id))
        if user_info._parent == None:
            output += f"`{user!s}` has no parent right now."
            await ctx.send(output)
            return
        else:
            parent = user_info.parent
            if len(parent._children) <= 1:
                output += f"`{user!s}` has no siblings on their side of the family."
            else:
                output += f"`{user!s}` has `{len(parent._children) - 1}` sibling" + \
                {False:"s", True:""}.get(len(parent._children)==2) + \
                " from their parent's side: " + \
                ", ".join([f"`{self.bot.get_user(i)!s}` (`{i}`)" for i in parent._children if i != user.id]) + '. '

        parent = user_info.parent
        if parent._partner == None:
            await ctx.send(output)
            return

        other_parent = parent.partner
        if len(other_parent._children) == 0:
            output += f"\nThey also have no siblings from their parent's partner's side of the family."
            await ctx.send(output)
            return

        output += f"\nThey also have `{len(other_parent._children)}` sibling" + \
        {False:"s", True:""}.get(len(other_parent._children)==1) + \
        " from their parent's partner's side of the family: " + \
        ", ".join([f"`{self.bot.get_user(i)!s}` (`{i}`)" for i in other_parent._children]) + '. '

        # Return all output
        await ctx.send(output)


    @command(aliases=['parents'])
    @bot_is_ready()
    @cooldown(1, 5, BucketType.user)
    async def parent(self, ctx:Context, user:User=None):
        '''
        Tells you who someone's parent is
        '''

        if user == None:
            user = ctx.author

        user_info = FamilyTreeMember.get(user.id, self.bot.get_tree_guild_id(ctx.guild.id))
        if user_info._parent == None:
            await ctx.send(f"`{user!s}` has no parent.")
            return
        await ctx.send(f"`{user!s}`'s parent is `{self.bot.get_user(user_info._parent)!s}` (`{user_info._parent}`).")


    @command(aliases=['relation'])
    @bot_is_ready()
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
        user, other = FamilyTreeMember.get(user.id, self.bot.get_tree_guild_id(ctx.guild.id)), FamilyTreeMember.get(other.id, self.bot.get_tree_guild_id(ctx.guild.id))
        relation = user.get_relation(other)

        username = await self.bot.get_name(user.id)
        othername = await self.bot.get_name(other.id)

        if relation == None:
            await ctx.send(f"`{username}` is not related to `{othername}`.")
            return
        await ctx.send(f"`{othername}` is `{username}`'s {relation}.")


    @command(aliases=['treesize','fs','ts'])
    @bot_is_ready()
    @cooldown(1, 5, BucketType.user)
    async def familysize(self, ctx:Context, user:User=None):
        '''
        Gives you the size of your family tree
        '''

        if user == None:
            user = ctx.author 
        user = FamilyTreeMember.get(user.id, self.bot.get_tree_guild_id(ctx.guild.id))
        span = user.span(expand_upwards=True, add_parent=True)
        username = await self.bot.get_name(user.id)
        await ctx.send(f"There are `{len(span)}` people in `{username}`'s family tree.")


    @command(enabled=False)
    @can_send_files()
    @no_tree_cache()
    @bot_is_ready()
    @cooldown(1, 5, BucketType.user)
    async def treefile(self, ctx:Context, root:Member=None):
        '''
        Gives you the full family tree of a user
        '''

        if root == None:
            root = ctx.author

        text = FamilyTreeMember.get(root.id, self.bot.get_tree_guild_id(ctx.guild.id)).generate_gedcom_script(self.bot)
        file = BytesIO(text.encode())
        await ctx.send(file=File(file, filename=f'Tree of {root.id}.ged'))


    @command(aliases=['familytree'], )
    @can_send_files()
    @no_tree_cache()
    @bot_is_ready()
    @cooldown(1, 60, BucketType.guild)
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
            raise e


    @command()
    @can_send_files()
    @no_tree_cache()
    @is_patreon()
    @bot_is_ready()
    @cooldown(1, 60, BucketType.guild)
    async def stupidtree(self, ctx:Context, root:User=None):
        '''
        Gets the family tree of a given user
        '''

        try:
            return await self.treemaker(ctx, root, stupid_tree=True)
        except Exception as e:
            raise e


    @command(aliases=['fulltree', 'ft', 'gt'], )
    @can_send_files()
    @no_tree_cache()
    @bot_is_ready()
    @cooldown(1, 60, BucketType.guild)
    async def globaltree(self, ctx:Context, root:User=None):
        '''
        Gets the global family tree of a given user
        '''

        try:
            return await self.treemaker(ctx, root, True)
        except Exception as e:
            raise e


    async def treemaker(self, ctx:Context, root:User, all_guilds:bool=False, stupid_tree:bool=False):

        if root == None:
            root = ctx.author
        root_user = root

        # Get their family tree
        tree = FamilyTreeMember.get(root_user.id, self.bot.get_tree_guild_id(ctx.guild.id))

        # Make sure they have one
        if tree.is_empty:
            await ctx.send(f"`{root_user!s}` has no family to put into a tree .-.")
            return
        await self.bot.tree_cache.add(ctx.author.id)
        m = await ctx.send("Generating tree - this may take a few minutes...")
        await ctx.channel.trigger_typing()

        # Write their treemaker code to a file
        ctu = await CustomisedTreeUser.get(ctx.author.id)
        if stupid_tree:
            dot_code = await tree.to_full_dot_script(self.bot, ctu)
        else:
            dot_code = await tree.to_dot_script(self.bot, None if all_guilds else ctx.guild, ctu)

        with open(f'{self.bot.config["tree_file_location"]}/{ctx.author.id}.gz', 'w', encoding='utf-8') as a:
            a.write(dot_code)

        # Convert to an image
        dot = await create_subprocess_exec(*[
            'dot', 
            '-Tpng', 
            f'{self.bot.config["tree_file_location"]}/{ctx.author.id}.gz', 
            '-o', 
            f'{self.bot.config["tree_file_location"]}/{ctx.author.id}.png', 
            '-Gcharset=UTF-8', 
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
            text = f"{ctx.author.mention}, " + choice([
                f"you can update how your tree looks with `{ctx.prefix}help customise` c:",
                f"feel free to help out the bot's development by `{ctx.prefix}donate`-ing c:",
                f"pitch in ideas, suggestions, and code help at `{ctx.prefix}git` c:",
                f"join the MarriageBot server at any time by running `{ctx.prefix}server` c:",
                f"know that whatever happens I love you very much c:",
                f"make sure to `{ctx.prefix}hug` and `{ctx.prefix}kiss` your partner! c:",
                f"vote for MarriageBot by running `{ctx.prefix}vote` c:",
            ])
            await ctx.send(text, file=file)
            await m.delete()
        except Exception:
            pass
        await self.bot.tree_cache.remove(ctx.author.id) 


def setup(bot:CustomBot):
    x = Information(bot)
    bot.add_cog(x)
