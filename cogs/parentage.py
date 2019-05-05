from re import compile
from asyncio import TimeoutError as AsyncTimeoutError, wait_for

from discord import Member, User
from discord.ext.commands import command, Context, cooldown
from discord.ext.commands import BadArgument, MissingRequiredArgument, CommandOnCooldown
from discord.ext.commands.cooldowns import BucketType

from cogs.utils.custom_bot import CustomBot
from cogs.utils.family_tree.family_tree_member import FamilyTreeMember
from cogs.utils.random_text.makeparent import MakeParentRandomText
from cogs.utils.random_text.adopt import AdoptRandomText
from cogs.utils.random_text.disown import DisownRandomText
from cogs.utils.random_text.emancipate import EmancipateRandomText
from cogs.utils.checks.user_block import BlockedUserError, UnblockedMember
from cogs.utils.checks.is_donator import is_patreon_predicate
from cogs.utils.acceptance_check import AcceptanceCheck
from cogs.utils.custom_cog import Cog


class Parentage(Cog):
    '''
    The parentage cog
    Handles the adoption of parents
    '''

    def __init__(self, bot:CustomBot):
        super().__init__(self.__class__.__name__)
        self.bot = bot


    async def cog_command_error(self, ctx:Context, error):
        '''
        Local error handler for the cog
        '''

        # Throw errors properly for me
        if ctx.author.id in self.bot.config['owners'] and not isinstance(error, CommandOnCooldown):
            text = f'```py\n{error}```'
            await ctx.send(text)
            raise error

        # Missing argument
        if isinstance(error, MissingRequiredArgument):
            await ctx.send("You need to specify a person for this command to work properly.")
            return

        # Cooldown
        elif isinstance(error, CommandOnCooldown):
            if ctx.author.id in self.bot.config['owners']:
                await ctx.reinvoke()
            else:
                await ctx.send(f"You can only use this command once every `{error.cooldown.per:.0f} seconds` per server. You may use this again in `{error.retry_after:.2f} seconds`.")
            return

        # Blocked user
        elif isinstance(error, BlockedUserError):
            await ctx.send("That user has blocked you, so you can't run this command.")
            return
    
        # Argument conversion error
        elif isinstance(error, BadArgument):
            try:
                argument_text = self.bot.bad_argument.search(str(error)).group(2)
                await ctx.send(f"User `{argument_text}` could not be found.")
            except AttributeError:
                await ctx.send(f"You are missing a required argument `User`.")
            return


    @command()
    @cooldown(1, 5, BucketType.user)
    async def makeparent(self, ctx:Context, *, parent:UnblockedMember):
        '''
        Picks a user that you want to be your parent
        '''

        # Set up some local variables
        instigator = ctx.author
        target = parent  # Just so "target" didn't show up in the help message

        # Manage output strings
        text_cog = self.bot.get_cog('MakeParentRandomText')
        template = self.bot.get_cog('TextTemplate')

        # Group the common denials
        text = template.process(text_cog, instigator, target)
        if text:
            await ctx.send(text) 
            return
        
        # Grab their family tree
        await ctx.trigger_typing()
        instigator_tree = await FamilyTreeMember.get(instigator.id, ctx.guild.id if ctx.guild.id in self.bot.server_specific_families else 0)
        target_tree = await FamilyTreeMember.get(target.id, ctx.guild.id if ctx.guild.id in self.bot.server_specific_families else 0)
        span = await instigator_tree.span(add_parent=True, expand_upwards=True)
        family_id_list = [i.id for i in span]

        # Manage more special text restrictions
        if target.id in family_id_list:
            await ctx.send(text_cog.target_is_family(instigator, target))
            return
        elif instigator_tree._parent:
            await ctx.send(text_cog.instigator_is_unqualified(instigator, target))
            return

        # Manage children
        is_patreon = await is_patreon_predicate(ctx.bot, instigator)
        children_amount = 30 if is_patreon else 15
        if len(user_tree._children) >= children_amount:
            await ctx.send({
                False: f"You can't have more than 15 children unless you're a Patreon donator (`{ctx.prefix}donate`)",
                True: f"You don't need more than 30 children. Please enter the Chill Zone:tm:.",
            }.get(is_patreon))
            return

        # Valid request
        if not target.bot:
            await ctx.send(text_cog.valid_target(instigator, target))
        self.bot.proposal_cache.add(instigator, target, 'MAKEPARENT')

        # Wait for a response 
        try:
            if target.bot: raise KeyError  # Auto-say yes
            check = AcceptanceCheck(target.id, ctx.channel.id).check
            m = await self.bot.wait_for('message', check=check, timeout=60.0)
            response = check(m)
        except AsyncTimeoutError as e:
            await ctx.send(text_cog.request_timeout(instigator, target), ignore_error=True)
            self.bot.proposal_cache.remove(instigator, target)
            return
        except KeyError as e:
            response = 'YES'
        self.bot.proposal_cache.remove(instigator, target)

        # Valid response recieved, see what their answer was
        if response == 'NO':
            await ctx.send(text_cog.request_denied(instigator, target))
            return 

        # They said yes - add to database
        async with self.bot.database() as db:
            try:
                await db('INSERT INTO parents (child_id, parent_id, guild_id) VALUES ($1, $2, $3)', instigator.id, target.id, ctx.guild.id if ctx.guild.id in self.bot.server_specific_families else 0)
            except Exception as e:
                return  # Only thrown when multiple people do at once, just return
        await ctx.send(text_cog.request_accepted(instigator, target), ignore_error=True)

        # Cache
        instigator_tree._parent = target.id 
        target_tree._children.append(instigator.id)


    @command()
    @cooldown(1, 5, BucketType.user)
    async def adopt(self, ctx:Context, *, parent:UnblockedMember):
        '''
        Adopt another user into your family
        '''

        instigator = ctx.author
        target = parent  # Just so "target" didn't show up in the help message

        # See if either user is already being proposed to
        if instigator.id in self.bot.proposal_cache:
            x = self.bot.proposal_cache.get(instigator.id)
            if x[0] == 'INSTIGATOR':
                await ctx.send(self.bot.get_cog('AdoptRandomText').instigator_is_instigator(instigator, target))
            elif x[0] == 'TARGET':
                await ctx.send(self.bot.get_cog('AdoptRandomText').instigator_is_target(instigator, target))
            return
        elif target.id in self.bot.proposal_cache:
            x = self.bot.proposal_cache.get(target.id)
            if x[0] == 'INSTIGATOR':
                await ctx.send(self.bot.get_cog('AdoptRandomText').target_is_instigator(instigator, target))
            elif x[0] == 'TARGET':
                await ctx.send(self.bot.get_cog('AdoptRandomText').target_is_target(instigator, target))
            return

        # Manage exclusions
        if target.id == self.bot.user.id:
            await ctx.send(self.bot.get_cog('AdoptRandomText').target_is_me(instigator, target))
            return
        elif target.bot or instigator.bot:
            await ctx.send(self.bot.get_cog('AdoptRandomText').target_is_bot(instigator, target))
            return
        elif instigator.id == target.id:
            await ctx.send(self.bot.get_cog('AdoptRandomText').target_is_you(instigator, target))
            return

        # Check current tree
        await ctx.trigger_typing()
        user_tree = await FamilyTreeMember.get(instigator.id, ctx.guild.id if ctx.guild.id in self.bot.server_specific_families else 0)

        # Manage children
        is_patreon = await is_patreon_predicate(ctx.bot, instigator)
        children_amount = 30 if is_patreon else 15
        if len(user_tree._children) >= children_amount:
            await ctx.send({
                False: f"You can't have more than 15 children unless you're a Patreon donator (`{ctx.prefix}donate`)",
                True: f"You don't need more than 30 children. Please enter the Chill Zone:tm:.",
            }.get(is_patreon))
            return

        # Make get_root awaitable
        root = await user_tree.get_root()
        span = await root.span(add_parent=True, expand_upwards=True)
        tree_id_list = [i.id for i in span]
        target_tree = await FamilyTreeMember.get(target.id, ctx.guild.id if ctx.guild.id in self.bot.server_specific_families else 0)

        # Manage more parent checks
        if target.id in tree_id_list:
            await ctx.send(self.bot.get_cog('AdoptRandomText').target_is_family(instigator, target))
            return
        elif target_tree._parent:
            await ctx.send(self.bot.get_cog('AdoptRandomText').target_is_unqualified(instigator, target))
            return

        # No parent, send request
        await ctx.send(self.bot.get_cog('AdoptRandomText').valid_target(instigator, target))
        self.bot.proposal_cache[instigator.id] = ('INSTIGATOR', 'ADOPT')
        self.bot.proposal_cache[target.id] = ('TARGET', 'ADOPT')

        # Wait for a response
        try:
            check = AcceptanceCheck(target.id, ctx.channel.id).check
            m = await self.bot.wait_for('message', check=check, timeout=60.0)
        except AsyncTimeoutError as e:
            try:
                await ctx.send(self.bot.get_cog('AdoptRandomText').request_timeout(instigator, target))
            except Exception as e:
                # If the bot was kicked, or access revoked, for example.
                pass
            self.bot.proposal_cache.remove(instigator.id)
            self.bot.proposal_cache.remove(target.id)
            return

        # Valid response recieved, see what their answer was
        response = check(m)
        if response == 'NO':
            await ctx.send(self.bot.get_cog('AdoptRandomText').request_denied(instigator, target))
        elif response == 'YES':
            async with self.bot.database() as db:
                try:
                    await db('INSERT INTO parents (parent_id, child_id, guild_id) VALUES ($1, $2, $3)', instigator.id, target.id, ctx.guild.id if ctx.guild.id in self.bot.server_specific_families else 0)
                except Exception as e:
                    return  # Only thrown when multiple people do at once, just return
            try:
                await ctx.send(self.bot.get_cog('AdoptRandomText').request_accepted(instigator, target))
            except Exception as e:
                pass
            me = await FamilyTreeMember.get(instigator.id, ctx.guild.id if ctx.guild.id in self.bot.server_specific_families else 0)
            me._children.append(target.id)
            them = await FamilyTreeMember.get(target.id, ctx.guild.id if ctx.guild.id in self.bot.server_specific_families else 0)
            them._parent = instigator.id

        self.bot.proposal_cache.remove(instigator.id)
        self.bot.proposal_cache.remove(target.id)


    @command(aliases=['abort'])
    @cooldown(1, 5, BucketType.user)
    async def disown(self, ctx:Context, *, child:User):
        '''
        Lets you remove a user from being your child
        '''

        instigator = ctx.author
        target = child

        user_tree = await FamilyTreeMember.get(instigator.id, ctx.guild.id if ctx.guild.id in self.bot.server_specific_families else 0)
        children_ids = user_tree._children

        if target.id not in children_ids:
            await ctx.send(self.bot.get_cog('DisownRandomText').invalid_target(instigator, target))
            return
        async with self.bot.database() as db:
            await db('DELETE FROM parents WHERE child_id=$1 AND parent_id=$2 AND guild_id=$3', target.id, instigator.id, ctx.guild.id if ctx.guild.id in self.bot.server_specific_families else 0)
        await ctx.send(self.bot.get_cog('DisownRandomText').valid_target(instigator, ctx.guild.get_member(child.id)))

        user_tree._children.remove(target.id)
        them = await FamilyTreeMember.get(target.id, ctx.guild.id if ctx.guild.id in self.bot.server_specific_families else 0)
        them._parent = None


    @command(aliases=['eman'])
    @cooldown(1, 5, BucketType.user)
    async def emancipate(self, ctx:Context):
        '''
        Making it so you no longer have a parent
        '''

        instigator = ctx.author

        user_tree = await FamilyTreeMember.get(instigator.id, ctx.guild.id if ctx.guild.id in self.bot.server_specific_families else 0)
        try:
            parent_id = user_tree._parent
        except AttributeError:
            await ctx.send(self.bot.get_cog('EmancipateRandomText').invalid_target(instigator, None))
            return

        async with self.bot.database() as db:
            await db('DELETE FROM parents WHERE parent_id=$1 AND child_id=$2 AND guild_id=$3', parent_id, instigator.id, ctx.guild.id if ctx.guild.id in self.bot.server_specific_families else 0)
        await ctx.send(self.bot.get_cog('EmancipateRandomText').valid_target(instigator, ctx.guild.get_member(parent_id)))

        user_tree._parent = None
        them = await FamilyTreeMember.get(parent_id, ctx.guild.id if ctx.guild.id in self.bot.server_specific_families else 0)
        them._children.remove(instigator.id)


def setup(bot:CustomBot):
    x = Parentage(bot)
    bot.add_cog(x)
