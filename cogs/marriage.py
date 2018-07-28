from re import compile
from asyncio import TimeoutError
from discord import Member
from discord.ext.commands import command, Context
from cogs.utils.custom_bot import CustomBot
from cogs.utils.family_tree.family_tree_member import FamilyTreeMember
import cogs.utils.random_text as random_text


class Marriage(object):
    '''
    The marriage cog
    Handles all marriage/divorce/etc commands
    '''

    def __init__(self, bot:CustomBot):
        self.bot = bot

        # Proposal text
        self.proposal_yes = compile(r"(i do)|(yes)|(of course)|(definitely)|(absolutely)|(yeah)|(yea)|(sure)|(m!accept)|")
        self.proposal_no = compile(r"(i don't)|(i dont)|(no)|(to think)|(i'm sorry)|(im sorry)")

        # Proposal cache
        self.cache = []


    @command(aliases=['marry'])
    async def propose(self, ctx:Context, user:Member):
        '''
        Lets you propose to another Discord user
        '''

        instigator = ctx.author
        target = user  # Just so "target" didn't show up in the help message

        # See if either user is already being proposed to
        if instigator.id in self.cache:
            await ctx.send("You can only propose to one person at a time .-.")
            return
        elif target.id in self.cache:
            await ctx.send("That person has already been proposed to. Please wait.")
            return

        # Manage exclusions
        if target.id == self.bot.user.id:
            await ctx.send("I'm flattered but no, sweetheart 😘")
            return
        elif target.bot or instigator.bot:
            await ctx.send("Gay marriage _was_ a slippery slope, but not quite slippery enough to let you marry robots. The answer is no.")
            return
        elif instigator.id == target.id:
            await ctx.send("Are you serious.")
            return

        # See if they're married or in the family already
        await ctx.trigger_typing()
        user_tree = FamilyTreeMember.get(instigator.id)
        root = user_tree.expand_backwards(-1)
        tree_id_list = [i.id for i in root.span(add_parent=True, expand_upwards=True)]

        if target.id in tree_id_list:
            await ctx.send(random_text.proposing_to_family(instigator, target))
            return
        if user_tree.partner:
            await ctx.send(random_text.proposing_when_married(instigator, target))
            return
        elif FamilyTreeMember.get(target.id).partner:
            await ctx.send(random_text.proposing_to_married(instigator, target))
            return

        # Neither are married, set up the proposal
        await ctx.send(random_text.valid_proposal(instigator, target))
        self.cache.append(instigator.id)
        self.cache.append(target.id)

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
            no = self.proposal_no.search(c)
            yes = self.proposal_yes.search(c)
            if any([yes, no]):
                return 'NO' if no else 'YES'
            return False

        # Wait for a response
        try:
            m = await self.bot.wait_for('message', check=check, timeout=60.0)
        except TimeoutError as e:
            await ctx.send(f"{instigator.mention}, your proposal has timed out. Try again when they're online!")
            self.cache.remove(instigator.id)
            self.cache.remove(target.id)
            return

        # Valid response recieved, see what their answer was
        response = check(m)
        if response == 'NO':
            await ctx.send("That's fair. The marriage has been called off.")
        elif response == 'YES':
            async with self.bot.database() as db:
                await db.marry(instigator, target)
            await ctx.send(f"{instigator.mention}, {target.mention}, I now pronounce you married.")
            me = FamilyTreeMember.get(instigator.id)
            me.partner = target.id 
            them = FamilyTreeMember.get(target.id)
            them.partner = instigator.id

        self.cache.remove(instigator.id)
        self.cache.remove(target.id)


    @command()
    async def divorce(self, ctx:Context, user:Member):
        '''
        Divorces you from your current spouse
        '''

        instigator = ctx.author
        target = user  # Just so "target" didn't show up in the help message

        # Get marriage data for the user
        instigator_data = FamilyTreeMember.get(instigator.id)

        # See why it could fail
        if instigator_data.partner == None:
            await ctx.send("You're not married. Don't try to divorce strangers .-.")
            return
        elif instigator_data.partner != target.id:
            await ctx.send("You aren't married to that person .-.")
            return

        # At this point they can only be married
        async with self.bot.database() as db:
            # await db.divorce(instigator=instigator, target=target, marriage_id=instigator_married[0]['marriage_id'])
            await db('UPDATE marriages SET valid=FALSE where user_id=$1 OR user_id=$2', instigator.id, target.id)
        await ctx.send(f"You and {target.mention} are now divorced. I wish you luck in your lives.")

        me = FamilyTreeMember.get(instigator.id)
        me.partner = None
        them = FamilyTreeMember.get(target.id)
        them.partner = None


def setup(bot:CustomBot):
    x = Marriage(bot)
    bot.add_cog(x)
