from re import compile
from asyncio import TimeoutError
from discord import Member
from discord.ext.commands import command, Context
from cogs.utils.custom_bot import CustomBot
from cogs.utils.family_tree.family_tree import FamilyTree
import cogs.utils.random_text as random_text


class Marriage(object):
    '''
    The marriage cog
    Handles all marriage/divorce/etc commands
    '''

    def __init__(self, bot:CustomBot):
        self.bot = bot

        # Proposal text
        self.proposal_yes = compile(r"(i do)|(yes)|(of course)|(definitely)|(absolutely)|(yeah)|(yea)|(sure)")
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
        async with self.bot.database() as db:
            instigator_married = await db.get_marriage(instigator)
            target_married = await db.get_marriage(target)
            family_tree1 = FamilyTree(instigator.id, 6, go_back=-1)  # Get the instigator's tree
            await family_tree1.populate_tree(db)
            family_tree2 = FamilyTree(target.id, 6, go_back=-1)  # Get the instigator's tree
            await family_tree2.populate_tree(db)
        
        # If they are, tell them off
        treeset_1 = set([i.id for i in family_tree1.all_users()])
        treeset_2 = set([i.id for i in family_tree2.all_users()])
        if treeset_1.intersection(treeset_2):
            await ctx.send(random_text.proposing_to_family(instigator, target))
            return
        if instigator_married:
            await ctx.send(random_text.proposing_when_married(instigator, target))
            return
        elif target_married:
            await ctx.send(random_text.proposing_to_married(instigator, target))
            return

        # Neither are married, set up the proposal
        async with self.bot.database() as db:
            await db.add_event(instigator=instigator, target=target, event='PROPOSAL')
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
            async with self.bot.database() as db:
                await db.add_event(instigator=target, target=instigator, event='TIMEOUT')
            await ctx.send(f"{instigator.mention}, your proposal has timed out. Try again when they're online!")
            self.cache.remove(instigator.id)
            self.cache.remove(target.id)
            return

        # Valid response recieved, see what their answer was
        response = check(m)
        if response == 'NO':
            async with self.bot.database() as db:
                await db.add_event(instigator=target, target=instigator, event='I DONT')
            await ctx.send("That's fair. The marriage has been called off.")
        elif response == 'YES':
            async with self.bot.database() as db:
                await db.add_event(instigator=target, target=instigator, event='I DO')
                await db.marry(instigator, target)
            await ctx.send(f"{instigator.mention}, {target.mention}, I now pronounce you married.")

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
        async with self.bot.database() as db:
            instigator_married = await db.get_marriage(instigator)

        # See why it could fail
        if not instigator_married:
            await ctx.send("You're not married. Don't try to divorce strangers .-.")
            return
        elif target.id not in [instigator_married[0]['partner_id'], instigator_married[1]['partner_id']]:
            await ctx.send("You aren't married to that person .-.")
            return

        # At this point they can only be married
        async with self.bot.database() as db:
            await db.divorce(instigator=instigator, target=target, marriage_id=instigator_married[0]['marriage_id'])
        await ctx.send(f"You and {target.mention} are now divorced. I wish you luck in your lives.")


def setup(bot:CustomBot):
    x = Marriage(bot)
    bot.add_cog(x)
