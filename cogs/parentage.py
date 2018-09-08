from re import compile
from asyncio import TimeoutError
from discord import Member, User
from discord.ext.commands import command, Context, cooldown
from discord.ext.commands.cooldowns import BucketType
from cogs.utils.custom_bot import CustomBot
from cogs.utils.family_tree.family_tree_member import FamilyTreeMember


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
        self.parentage_random_text = None
        self.bot.loop.create_task(self.get_parentage_random_text())

    
    async def get_parentage_random_text(self):
        await self.bot.wait_until_ready()
        self.parentage_random_text = self.bot.cogs.get('ParentageRandomText')


    def __local_check(self, ctx:Context):
        return self.parentage_random_text != None


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
                await ctx.send(self.parentage_random_text.parent_while_instigator(instigator, target))
            elif x[0] == 'TARGET':
                await ctx.send(self.parentage_random_text.parent_while_target(instigator, target))
            return
        elif target.id in self.bot.proposal_cache:
            x = self.bot.proposal_cache.get(target.id)
            if x[0] == 'INSTIGATOR':
                await ctx.send(self.parentage_random_text.parent_to_instigator(instigator, target))
            elif x[0] == 'TARGET':
                await ctx.send(self.parentage_random_text.parent_to_target(instigator, target))
            return

        # Manage exclusions
        if target.id == self.bot.user.id:
            await ctx.send(self.parentage_random_text.parent_is_me(instigator, target))
            return
        elif instigator.bot:
            # Silently deny robots
            return
        elif instigator.id == target.id:
            await ctx.send(self.parentage_random_text.parent_yourself(instigator, target))
            return

        # See if they already have a parent
        await ctx.trigger_typing()
        user_tree = FamilyTreeMember.get(instigator.id)
        root = user_tree.expand_backwards(-1)
        tree_id_list = [i.id for i in root.span(add_parent=True, expand_upwards=True)]

        if target.id in tree_id_list:
            await ctx.send(self.parentage_random_text.parent_is_family(instigator, target))
            return
        elif user_tree.parent:
            await ctx.send(self.parentage_random_text.parent_while_adopted(instigator, target))
            return

        # No parent, send request
        if not target.bot:
            await ctx.send(self.parentage_random_text.valid_parent_choice(instigator, target))
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
                await ctx.send(self.parentage_random_text.parent_request_timeout(instigator, target))
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
            await ctx.send(self.parentage_random_text.parent_request_deny(instigator, target))
        elif response == 'YES':
            async with self.bot.database() as db:
                try:
                    await db('INSERT INTO parents (child_id, parent_id) VALUES ($1, $2)', instigator.id, target.id)
                except Exception as e:
                    return  # Only thrown when multiple people do at once, just return
            try:
                await ctx.send(self.parentage_random_text.parent_request_accept(instigator, target))
            except Exception as e:
                pass
            me = FamilyTreeMember.get(instigator.id)
            me.parent = target.id 
            them = FamilyTreeMember.get(target.id)
            them.children.append(instigator.id)

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
            await ctx.send("You can only make or recieve one proposition at a time.")
            return
        elif target.id in self.bot.proposal_cache:
            await ctx.send("That person has already recieved or made a proposition. Please wait.")
            return

        # Manage exclusions
        if target.id == self.bot.user.id:
            await ctx.send("I'm flattered but no, sweetheart 😘")
            return
        elif target.bot or instigator.bot:
            await ctx.send("Robots don't make particularly good children.")
            return
        elif instigator.id == target.id:
            await ctx.send("Are you serious.")
            return

        # See if they already have a parent
        await ctx.trigger_typing()
        user_tree = FamilyTreeMember.get(instigator.id)
        root = user_tree.expand_backwards(-1)
        tree_id_list = [i.id for i in root.span(add_parent=True, expand_upwards=True)]

        if target.id in tree_id_list:
            await ctx.send(f"{instigator.mention}, they're already part of your family.")
            return
        elif FamilyTreeMember.get(target.id).parent:
            await ctx.send(f"Sorry, but `{target!s}` already has a parent.")
            return

        # No parent, send request
        await ctx.send(f"{target.mention}, do you want to be {instigator.mention}'s child?")
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
                await ctx.send(f"{instigator.mention}, your adoption request has timed out. Try again when they're online!")
            except Exception as e:
                # If the bot was kicked, or access revoked, for example.
                pass
            self.bot.proposal_cache.remove(instigator.id)
            self.bot.proposal_cache.remove(target.id)
            return

        # Valid response recieved, see what their answer was
        response = check(m)
        if response == 'NO':
            await ctx.send("No adoption today, it seems..")
        elif response == 'YES':
            async with self.bot.database() as db:
                try:
                    await db('INSERT INTO parents (parent_id, child_id) VALUES ($1, $2)', instigator.id, target.id)
                except Exception as e:
                    return  # Only thrown when multiple people do at once, just return
            try:
                await ctx.send(f"{target.mention}, your new parent is {instigator.mention} c:")
            except Exception as e:
                pass
            me = FamilyTreeMember.get(instigator.id)
            me.children.append(target.id)
            them = FamilyTreeMember.get(target.id)
            them.parent = instigator.id

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
        children_ids = user_tree.children

        if target.id not in children_ids:
            await ctx.send(f"That person isn't your child, {instigator.mention}.")
            return
        async with self.bot.database() as db:
            await db('DELETE FROM parents WHERE child_id=$1 AND parent_id=$2', target.id, instigator.id)
        if ctx.guild.get_member(child.id):            
            await ctx.send(f"Sorry, {target.mention}, but you're an orphan now. You're free, {instigator.mention}!")
        else:
            await ctx.send(f"You're free, {instigator.mention}, they're no longer your child!")

        me = FamilyTreeMember.get(instigator.id)
        me.children.remove(target.id)
        them = FamilyTreeMember.get(target.id)
        them.parent = None


    @command(aliases=['eman'])
    @cooldown(1, 5, BucketType.user)
    async def emancipate(self, ctx:Context):
        '''
        Making it so you no longer have a parent
        '''

        instigator = ctx.author

        user_tree = FamilyTreeMember.get(instigator.id)
        parent = user_tree.parent

        if parent == None:
            await ctx.send(f"You don't have a parent, {instigator.mention}")
            return
        target = self.bot.get_user(parent)

        async with self.bot.database() as db:
            await db('DELETE FROM parents WHERE parent_id=$1 AND child_id=$2', target.id, instigator.id)
        if ctx.guild.get_member(target.id):
            await ctx.send(f"You're an orphan now, {instigator.mention}. Sorry {target.mention}!")
        else:
            await ctx.send(f"You're an orphan now, {instigator.mention}.")

        me = FamilyTreeMember.get(instigator.id)
        me.parent = None
        them = FamilyTreeMember.get(target.id)
        them.children.remove(instigator.id)


def setup(bot:CustomBot):
    x = Parentage(bot)
    bot.add_cog(x)
