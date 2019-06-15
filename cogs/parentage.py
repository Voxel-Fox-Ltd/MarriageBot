from asyncio import TimeoutError as AsyncTimeoutError
from asyncio import wait_for
from re import compile
from typing import Union

from discord import Member, User
from discord.ext.commands import (BadArgument, CommandOnCooldown, Context,
                                  MissingRequiredArgument, command, cooldown)
from discord.ext.commands.cooldowns import BucketType

from cogs.utils.acceptance_check import AcceptanceCheck
from cogs.utils.checks.bot_is_ready import BotNotReady, bot_is_ready
from cogs.utils.checks.is_donator import is_patreon_predicate, is_patreon, IsNotDonator
from cogs.utils.checks.user_block import BlockedUserError, UnblockedMember
from cogs.utils.custom_bot import CustomBot
from cogs.utils.custom_cog import Cog
from cogs.utils.family_tree.family_tree_member import FamilyTreeMember
from cogs.utils.random_text.adopt import AdoptRandomText
from cogs.utils.random_text.disown import DisownRandomText
from cogs.utils.random_text.emancipate import EmancipateRandomText
from cogs.utils.random_text.makeparent import MakeParentRandomText


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
        if ctx.author.id in self.bot.config['owners'] and not isinstance(error, CommandOnCooldown, IsNotDonator):
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

        # Bot ready
        elif isinstance(error, BotNotReady):
            await ctx.send("The bot isn't ready to start processing that command yet - please wait.")
            return

        # Donator
        elif isinstance(error, IsNotDonator):
            # Bypass for owner
            if ctx.author.id in self.bot.config['owners']:
                await ctx.reinvoke()
            else:
                await ctx.send(f"You need to be a Patreon subscriber (`{ctx.prefix}donate`) to be able to run this command.")
            return


    @command()
    @bot_is_ready()
    @cooldown(1, 5, BucketType.user)
    async def makeparent(self, ctx:Context, *, target:UnblockedMember):
        '''
        Picks a user that you want to be your parent
        '''

        # Variables we're gonna need for later
        instigator = ctx.author
        if instigator.bot: return
        instigator_tree = FamilyTreeMember.get(instigator.id, self.bot.get_tree_guild_id(ctx.guild.id))
        target_tree = FamilyTreeMember.get(target.id, self.bot.get_tree_guild_id(ctx.guild.id))

        # Manage output strings
        text_processor = MakeParentRandomText(self.bot)
        text = text_processor.process(instigator, target)
        if text:
            await ctx.send(text) 
            return
        
        # See if our user already has a parent
        if instigator_tree._parent:
            await ctx.send(text_processor.instigator_is_unqualified(instigator, target))
            return

        # See if they're already related
        if instigator_tree.get_relation(target_tree):
            await ctx.send(text_processor.target_is_family(instigator, target))
            return

        # Manage children
        is_patreon = await is_patreon_predicate(ctx.bot, target)
        children_amount = 30 if is_patreon else 15
        if len(target_tree._children) >= children_amount:
            await ctx.send({
                False: f"You can't have more than 15 children unless you're a Patreon donator (`{ctx.prefix}donate`)",
                True: f"You don't need more than 30 children. Please enter the Chill Zone:tm:.",
            }.get(is_patreon))
            return

        # Valid request
        if not target.bot:
            await ctx.send(text_processor.valid_target(instigator, target))
        await self.bot.proposal_cache.add(instigator, target, 'MAKEPARENT')

        # Wait for a response 
        try:
            if target.bot: raise KeyError  # Auto-say yes
            check = AcceptanceCheck(target.id, ctx.channel.id).check
            m = await self.bot.wait_for('message', check=check, timeout=60.0)
            response = check(m)
        except AsyncTimeoutError as e:
            await ctx.send(text_processor.request_timeout(instigator, target), ignore_error=True)
        except KeyError as e:
            response = 'YES'

        # Valid response recieved, see what their answer was
        if response == 'NO':
            await ctx.send(text_processor.request_denied(instigator, target), ignore_error=True)
            await self.bot.proposal_cache.remove(instigator, target)
            return 

        # They said yes - add to database
        async with self.bot.database() as db:
            try:
                await db('INSERT INTO parents (child_id, parent_id, guild_id) VALUES ($1, $2, $3)', instigator.id, target.id, ctx.guild.id if ctx.guild.id in self.bot.server_specific_families else 0)
            except Exception as e:
                raise e
                return  # Only thrown when multiple people do at once, just return
        await ctx.send(text_processor.request_accepted(instigator, target), ignore_error=True)

        # Cache
        instigator_tree._parent = target.id 
        target_tree._children.append(instigator.id)

        # Ping em off over redis
        async with self.bot.redis() as re:
            await re.publish_json('TreeMemberUpdate', instigator_tree.to_json())
            await re.publish_json('TreeMemberUpdate', target_tree.to_json())

        # Uncache
        await self.bot.proposal_cache.remove(instigator, target)


    @command()
    @bot_is_ready()
    @cooldown(1, 5, BucketType.user)
    async def adopt(self, ctx:Context, *, target:UnblockedMember):
        '''
        Adopt another user into your family
        '''

        # Variables we're gonna need for later
        instigator = ctx.author
        if instigator.bot: return
        instigator_tree = FamilyTreeMember.get(instigator.id, self.bot.get_tree_guild_id(ctx.guild.id))
        target_tree = FamilyTreeMember.get(target.id, self.bot.get_tree_guild_id(ctx.guild.id))

        # Manage output strings
        text_processor = AdoptRandomText(self.bot)
        text = text_processor.process(instigator, target)
        if text:
            await ctx.send(text) 
            return
        
        # See if our user already has a parent
        if target_tree._parent:
            await ctx.send(text_processor.target_is_unqualified(instigator, target))
            return

        # See if they're already related
        if instigator_tree.get_relation(target_tree):
            await ctx.send(text_processor.target_is_family(instigator, target))
            return

        # Manage children
        is_patreon = await is_patreon_predicate(ctx.bot, instigator)
        children_amount = 30 if is_patreon else 15
        if len(instigator_tree._children) >= children_amount:
            await ctx.send({
                False: f"You can't have more than 15 children unless you're a Patreon donator (`{ctx.prefix}donate`)",
                True: f"You don't need more than 30 children. Please enter the Chill Zone:tm:.",
            }.get(is_patreon))
            return

        # No parent, send request
        await ctx.send(text_processor.valid_target(instigator, target))
        await self.bot.proposal_cache.add(instigator, target, 'ADOPT')

        # Wait for a response
        try:
            check = AcceptanceCheck(target.id, ctx.channel.id).check
            m = await self.bot.wait_for('message', check=check, timeout=60.0)
        except AsyncTimeoutError as e:
            await ctx.send(text_processor.request_timeout(instigator, target), ignore_error=True)
            await self.bot.proposal_cache.remove(instigator, target)
            return

        # Valid response recieved, see what their answer was
        response = check(m)
        if response == 'NO':
            await ctx.send(text_processor.request_denied(instigator, target), ignore_error=True)
            await self.bot.proposal_cache.remove(instigator, target)
            return
            
        # Database it up
        async with self.bot.database() as db:
            try:
                await db('INSERT INTO parents (parent_id, child_id, guild_id) VALUES ($1, $2, $3)', instigator.id, target.id, ctx.guild.id if ctx.guild.id in self.bot.server_specific_families else 0)
            except Exception as e:
                # child_data = await db('SELECT FROM parents WHERE child_id=$1 AND guild_id=$2', target.id, ctx.guild.id if ctx.guild.id in self.bot.server_specific_families else 0)
                # if child_data:
                #     target_tree._parent = child_data[0]['parent_id']
                #     await ctx.send("Apparently this user already had a parent that I didn't quite see. Oops!")
                #     return
                # raise e 
                pass

        # Add family caching
        instigator_tree._children.append(target.id)
        target_tree._parent = instigator_tree.id

        # Ping em off over redis
        async with self.bot.redis() as re:
            await re.publish_json('TreeMemberUpdate', instigator_tree.to_json())
            await re.publish_json('TreeMemberUpdate', target_tree.to_json())

        # Uncache
        await self.bot.proposal_cache.remove(instigator, target)

        # Output to user
        await ctx.send(text_processor.request_accepted(instigator, target), ignore_error=True)


    @command(aliases=['abort'])
    @bot_is_ready()
    @cooldown(1, 5, BucketType.user)
    async def disown(self, ctx:Context, *, target:Union[User, int, str]):
        '''
        Lets you remove a user from being your child
        '''

        # Manage output strings
        text_processor = DisownRandomText(self.bot)

        # Variables we're gonna need for later
        instigator = ctx.author
        if instigator.bot: return
        instigator_tree = FamilyTreeMember.get(instigator.id, self.bot.get_tree_guild_id(ctx.guild.id))
        target_tree = None

        # Run target converter to get target's tree
        if isinstance(target, User):
            target_tree = FamilyTreeMember.get(target.id, self.bot.get_tree_guild_id(ctx.guild.id))

        # If they're an ID
        elif isinstance(target, int):
            try:
                target_tree = instigator_tree.children[instigator_tree._children.index(target)]
            except ValueError:
                await ctx.send(text_processor.instigator_is_unqualified(instigator, target if isinstance(target, User) else None))
                return 

        # If they're a name
        elif isinstance(target, str):
            child_ids = instigator_tree._children
            child_names = []
            async with self.bot.redis() as re:
                for c, i in enumerate(child_ids):
                    name = await re.get(f'UserName-{i}')
                    if target == name:
                        target_tree = instigator_tree.children[c]
                        break 
            if target_tree == None:
                await ctx.send(text_processor.instigator_is_unqualified(instigator, None))
                return 

        # Make sure they're the child of the instigator
        if not target_tree.id in instigator_tree._children:
            await ctx.send(text_processor.instigator_is_unqualified(instigator, ctx.guild.get_member(target_tree.id)))
            return 
        
        # Oh hey they are - remove from database
        async with self.bot.database() as db:
            await db('DELETE FROM parents WHERE child_id=$1 AND parent_id=$2 AND guild_id=$3', target_tree.id, instigator.id, instigator_tree._guild_id)
        await ctx.send(text_processor.valid_target(instigator, ctx.guild.get_member(target_tree.id)), ignore_error=True)

        # Remove family caching
        instigator_tree._children.remove(target_tree.id)
        target_tree._parent = None

        # Ping em off over redis
        async with self.bot.redis() as re:
            await re.publish_json('TreeMemberUpdate', instigator_tree.to_json())
            await re.publish_json('TreeMemberUpdate', target_tree.to_json())


    @command(aliases=['eman'])
    @bot_is_ready()
    @cooldown(1, 5, BucketType.user)
    async def emancipate(self, ctx:Context):
        '''
        Making it so you no longer have a parent
        '''

        # Variables we're gonna need for later
        instigator = ctx.author
        if instigator.bot: return
        instigator_tree = FamilyTreeMember.get(instigator.id, self.bot.get_tree_guild_id(ctx.guild.id))

        # Manage output strings
        text_processor = EmancipateRandomText(self.bot)

        # Make sure they're the child of the instigator
        if not instigator_tree._parent:
            await ctx.send(text_processor.instigator_is_unqualified(instigator))
            return 

        # They do have a parent, yes
        target_tree = instigator_tree.parent

        # Remove family caching
        instigator_tree._parent = None
        target_tree._children.remove(instigator.id)

        # Ping em off over redis
        async with self.bot.redis() as re:
            await re.publish_json('TreeMemberUpdate', instigator_tree.to_json())
            await re.publish_json('TreeMemberUpdate', target_tree.to_json())

        # Oh hey they are - remove from database
        async with self.bot.database() as db:
            await db('DELETE FROM parents WHERE parent_id=$1 AND child_id=$2 AND guild_id=$3', target_tree.id, instigator.id, instigator_tree._guild_id)
        v = text_processor.valid_target(instigator)
        await ctx.send(v)


    @command()
    @is_patreon()
    async def disownall(self, ctx:Context):
        '''Disowns all of your children'''

        # Get their children
        if ctx.author.bot: return
        user_tree = FamilyTreeMember.get(ctx.author.id, self.bot.get_tree_guild_id(ctx.guild.id))
        children = user_tree.children[:]
        if not children:
            await ctx.send("You don't have any children to disown .-.") # TODO make this text into a template
            return
        
        # Disown em
        for child in children:
            child._parent = None 
        user_tree.children = [] 

        # Save em
        async with self.bot.database() as db:
            for child in children:
                await db('DELETE FROM parents WHERE parent_id=$1 AND child_id=$2 AND guild_id=$3', user_tree.id, child.id, user_tree._guild_id)
        
        # Redis em
        async with self.bot.redis() as re:
            for person in children + [user_tree]:
                await re.publish_json('TreeMemberUpdate', person.to_json())
        
        # Output to user
        await ctx.send("You've sucessfully disowned all of your children.")  # TODO


def setup(bot:CustomBot):
    x = Parentage(bot)
    bot.add_cog(x)
