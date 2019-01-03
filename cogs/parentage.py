from re import compile
from asyncio import TimeoutError, wait_for

from discord import Member, User
from discord.ext.commands import command, Context, cooldown
from discord.ext.commands.cooldowns import BucketType

from cogs.utils.custom_bot import CustomBot
from cogs.utils.family_tree.family_tree_member import FamilyTreeMember
from cogs.utils.random_text.makeparent import MakeParentRandomText
from cogs.utils.random_text.adopt import AdoptRandomText
from cogs.utils.random_text.disown import DisownRandomText
from cogs.utils.random_text.emancipate import EmancipateRandomText


class Parentage(object):
    '''
    The parentage cog
    Handles the adoption of parents
    '''

    def __init__(self, bot:CustomBot):
        self.bot = bot

        # Proposal text
        self.proposal_yes = compile(r"(i do)|(yes)|(of course)|(definitely)|(absolutely)|(yeah)|(yea)|(sure)")
        self.proposal_no = compile(r"(i don't)|(i dont)|(no)|(to think)|(i'm sorry)|(im sorry)")

        # Get random text for this cog
        self.makeparent_random_text = None
        self.adopt_random_text = None
        self.disown_random_text = None
        self.emancipate_random_text = None
        self.bot.loop.create_task(self.get_makeparent_random_text())
        self.bot.loop.create_task(self.get_adopt_random_text())
        self.bot.loop.create_task(self.get_disown_random_text())
        self.bot.loop.create_task(self.get_emancipate_random_text())

    
    async def get_makeparent_random_text(self):
        await self.bot.wait_until_ready()
        self.makeparent_random_text = self.bot.cogs.get('MakeParentRandomText')

    
    async def get_adopt_random_text(self):
        await self.bot.wait_until_ready()
        self.adopt_random_text = self.bot.cogs.get('AdoptRandomText')

    
    async def get_disown_random_text(self):
        await self.bot.wait_until_ready()
        self.disown_random_text = self.bot.cogs.get('DisownRandomText')

    
    async def get_emancipate_random_text(self):
        await self.bot.wait_until_ready()
        self.emancipate_random_text = self.bot.cogs.get('EmancipateRandomText')


    def __local_check(self, ctx:Context):
        return all([
            self.makeparent_random_text != None,
            self.adopt_random_text != None,
            self.disown_random_text != None,
            self.emancipate_random_text != None,
        ])


    @command()
    @cooldown(1, 5, BucketType.user)
    async def makeparent(self, ctx:Context, parent:Member):
        '''
        Picks a user that you want to be your parent
        '''

        instigator = ctx.author
        target = parent  # Just so "target" didn't show up in the help message

        # See if either user is already being proposed to
        if instigator.id in self.bot.proposal_cache:
            x = self.bot.proposal_cache.get(instigator.id)
            if x[0] == 'INSTIGATOR':
                await ctx.send(self.makeparent_random_text.instigator_is_instigator(instigator, target))
            elif x[0] == 'TARGET':
                await ctx.send(self.makeparent_random_text.instigator_is_target(instigator, target))
            return
        elif target.id in self.bot.proposal_cache:
            x = self.bot.proposal_cache.get(target.id)
            if x[0] == 'INSTIGATOR':
                await ctx.send(self.makeparent_random_text.target_is_instigator(instigator, target))
            elif x[0] == 'TARGET':
                await ctx.send(self.makeparent_random_text.target_is_target(instigator, target))
            return

        # Manage exclusions
        if target.id == self.bot.user.id:
            await ctx.send(self.makeparent_random_text.target_is_me(instigator, target))
            return
        elif instigator.bot:
            # Silently deny robots
            return
        elif instigator.id == target.id:
            await ctx.send(self.makeparent_random_text.target_is_you(instigator, target))
            return

        # See if they already have a parent
        await ctx.trigger_typing()
        user_tree = FamilyTreeMember.get(instigator.id)
        root = user_tree.get_root()
        tree_id_list = [i.id for i in root.span(add_parent=True, expand_upwards=True)]

        if target.id in tree_id_list:
            await ctx.send(self.makeparent_random_text.target_is_family(instigator, target))
            return
        elif user_tree.parent:
            await ctx.send(self.makeparent_random_text.instigator_is_unqualified(instigator, target))
            return

        # No parent, send request
        if not target.bot:
            await ctx.send(self.makeparent_random_text.valid_target(instigator, target))
        self.bot.proposal_cache[instigator.id] = ('INSTIGATOR', 'MAKEPARENT')
        self.bot.proposal_cache[target.id] = ('TARGET', 'MAKEPARENT')

        # Make the check
        def check(message):
            '''
            The check to make sure that the user is giving a valid yes/no
            when provided with a proposal
            '''
            
            if message.author.id != target.id:
                return False
            if message.channel.id != ctx.channel.id:
                return False
            c = message.content.casefold()
            if not c:
                return False
            no = self.proposal_no.search(c)
            yes = self.proposal_yes.search(c)
            if any([yes, no]):
                return 'NO' if no else 'YES'
            return False

        # Wait for a response
        try:
            if target.bot:
                raise KeyError
            m = await self.bot.wait_for('message', check=check, timeout=60.0)
            response = check(m)
        except TimeoutError as e:
            try:
                await ctx.send(self.makeparent_random_text.request_timeout(instigator, target))
            except Exception as e:
                # If the bot was kicked, or access revoked, for example.
                pass
            self.bot.proposal_cache.remove(instigator.id)
            self.bot.proposal_cache.remove(target.id)
            return
        except KeyError as e:
            response = 'YES'

        # Valid response recieved, see what their answer was
        if response == 'NO':
            await ctx.send(self.makeparent_random_text.request_denied(instigator, target))
        elif response == 'YES':
            async with self.bot.database() as db:
                try:
                    await db('INSERT INTO parents (child_id, parent_id) VALUES ($1, $2)', instigator.id, target.id)
                except Exception as e:
                    return  # Only thrown when multiple people do at once, just return
            try:
                await ctx.send(self.makeparent_random_text.request_accepted(instigator, target))
            except Exception as e:
                pass
            me = FamilyTreeMember.get(instigator.id)
            me._parent = target.id 
            them = FamilyTreeMember.get(target.id)
            them._children.append(instigator.id)

        self.bot.proposal_cache.remove(instigator.id)
        self.bot.proposal_cache.remove(target.id)


    @command()
    @cooldown(1, 5, BucketType.user)
    async def adopt(self, ctx:Context, parent:Member):
        '''
        Adopt another user into your family
        '''

        instigator = ctx.author
        target = parent  # Just so "target" didn't show up in the help message

        # See if either user is already being proposed to
        if instigator.id in self.bot.proposal_cache:
            x = self.bot.proposal_cache.get(instigator.id)
            if x[0] == 'INSTIGATOR':
                await ctx.send(self.adopt_random_text.instigator_is_instigator(instigator, target))
            elif x[0] == 'TARGET':
                await ctx.send(self.adopt_random_text.instigator_is_target(instigator, target))
            return
        elif target.id in self.bot.proposal_cache:
            x = self.bot.proposal_cache.get(target.id)
            if x[0] == 'INSTIGATOR':
                await ctx.send(self.adopt_random_text.target_is_instigator(instigator, target))
            elif x[0] == 'TARGET':
                await ctx.send(self.adopt_random_text.target_is_target(instigator, target))
            return

        # Manage exclusions
        if target.id == self.bot.user.id:
            await ctx.send(self.adopt_random_text.target_is_me(instigator, target))
            return
        elif target.bot or instigator.bot:
            await ctx.send(self.adopt_random_text.target_is_bot(instigator, target))
            return
        elif instigator.id == target.id:
            await ctx.send(self.adopt_random_text.target_is_you(instigator, target))
            return

        # Check current tree
        await ctx.trigger_typing()
        user_tree = FamilyTreeMember.get(instigator.id)
        if len(user_tree._children) >= 30:
            await ctx.send("You don't need more than 30 children. Please enter the chill zone.")
            return

        # Make get_root awaitable
        awaitable_root = self.bot.loop.run_in_executor(None, user_tree.get_root)
        try:
            root = await wait_for(awaitable_root, timeout=10.0, loop=self.bot.loop)
        except TimeoutError:
            await ctx.send("The `get_root` method for your family tree has failed. This is usually due to a loop somewhere in your tree.")
            return
        tree_id_list = [i.id for i in root.span(add_parent=True, expand_upwards=True)]

        if target.id in tree_id_list:
            await ctx.send(self.adopt_random_text.target_is_family(instigator, target))
            return
        elif FamilyTreeMember.get(target.id).parent:
            await ctx.send(self.adopt_random_text.target_is_unqualified(instigator, target))
            return

        # No parent, send request
        await ctx.send(self.adopt_random_text.valid_target(instigator, target))
        self.bot.proposal_cache[instigator.id] = ('INSTIGATOR', 'ADOPT')
        self.bot.proposal_cache[target.id] = ('TARGET', 'ADOPT')

        # Make the check
        def check(message):
            '''
            The check to make sure that the user is giving a valid yes/no
            when provided with a proposal
            '''
            
            if message.author.id != target.id:
                return False
            if message.channel.id != ctx.channel.id:
                return False
            c = message.content.casefold()
            if not c:
                return False
            no = self.proposal_no.search(c)
            yes = self.proposal_yes.search(c)
            if any([yes, no]):
                return 'NO' if no else 'YES'
            return False

        # Wait for a response
        try:
            m = await self.bot.wait_for('message', check=check, timeout=60.0)
        except TimeoutError as e:
            try:
                await ctx.send(self.adopt_random_text.request_timeout(instigator, target))
            except Exception as e:
                # If the bot was kicked, or access revoked, for example.
                pass
            self.bot.proposal_cache.remove(instigator.id)
            self.bot.proposal_cache.remove(target.id)
            return

        # Valid response recieved, see what their answer was
        response = check(m)
        if response == 'NO':
            await ctx.send(self.adopt_random_text.request_denied(instigator, target))
        elif response == 'YES':
            async with self.bot.database() as db:
                try:
                    await db('INSERT INTO parents (parent_id, child_id) VALUES ($1, $2)', instigator.id, target.id)
                except Exception as e:
                    return  # Only thrown when multiple people do at once, just return
            try:
                await ctx.send(self.adopt_random_text.request_accepted(instigator, target))
            except Exception as e:
                pass
            me = FamilyTreeMember.get(instigator.id)
            me._children.append(target.id)
            them = FamilyTreeMember.get(target.id)
            them._parent = instigator.id

        self.bot.proposal_cache.remove(instigator.id)
        self.bot.proposal_cache.remove(target.id)


    @command(aliases=['abort'])
    @cooldown(1, 5, BucketType.user)
    async def disown(self, ctx:Context, child:User):
        '''
        Lets you remove a user from being your child
        '''

        instigator = ctx.author
        target = child

        user_tree = FamilyTreeMember.get(instigator.id)
        children_ids = user_tree._children

        if target.id not in children_ids:
            await ctx.send(self.disown_random_text.invalid_target(instigator, target))
            return
        async with self.bot.database() as db:
            await db('DELETE FROM parents WHERE child_id=$1 AND parent_id=$2', target.id, instigator.id)
        await ctx.send(self.disown_random_text.valid_target(instigator, ctx.guild.get_member(child.id)))

        me = FamilyTreeMember.get(instigator.id)
        me._children.remove(target.id)
        them = FamilyTreeMember.get(target.id)
        them._parent = None


    @command(aliases=['eman'])
    @cooldown(1, 5, BucketType.user)
    async def emancipate(self, ctx:Context):
        '''
        Making it so you no longer have a parent
        '''

        instigator = ctx.author

        user_tree = FamilyTreeMember.get(instigator.id)
        try:
            parent_id = user_tree.parent.id
        except AttributeError:
            await ctx.send(self.emancipate_random_text.invalid_target(instigator, None))
            return

        async with self.bot.database() as db:
            await db('DELETE FROM parents WHERE parent_id=$1 AND child_id=$2', parent_id, instigator.id)
        await ctx.send(self.emancipate_random_text.valid_target(instigator, ctx.guild.get_member(parent_id)))

        me = FamilyTreeMember.get(instigator.id)
        me._parent = None
        them = FamilyTreeMember.get(parent_id)
        them._children.remove(instigator.id)


def setup(bot:CustomBot):
    x = Parentage(bot)
    bot.add_cog(x)
