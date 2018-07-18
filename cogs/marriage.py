from re import compile
from asyncio import TimeoutError
from discord import Member
from discord.ext.commands import command, Context
from cogs.utils.custom_bot import CustomBot


class Marriage(object):
    '''
    The marriage cog
    Handles all marriage/divorce/etc commands
    '''

    def __init__(self, bot:CustomBot):
        self.bot = bot
        self.proposal_yes = compile(r"(i do)|(yes)|(of course)|(definitely)|(absolutely)|(yeah)|(yea)")
        self.proposal_no = compile(r"(i don't)|(i dont)|(no)|(to think)|(i'm sorry)|(im sorry)")


    @command()
    async def propose(self, ctx:Context, user:Member):
        '''
        Lets you propose to another Discord user
        '''

        instigator = ctx.author
        target = user  # Just so "target" didn't show up in the help message
        if target.bot:
            await ctx.send("Gay marriage _was_ a slippery slope, but not quite slippery enough to let you marry robots. The answer is no.")
            return
        if instigator.id == target.id:
            await ctx.send("Are you serious.")
            return

        async with self.bot.database() as db:
            # See if they're married already
            instigator_married = await db.get_marriage(instigator)
            target_married = await db.get_marriage(target)

        # If they are, tell them off
        if instigator_married:
            await ctx.send(f"{instigator.mention}, you can't marry someone if you're already married .-.")
            return
        elif target_married:
            async with self.bot.database() as db:
                await db.add_event(instigator=instigator, target=target, event='PROPOSAL')
                await db.add_event(instigator=target, target=instigator, event='ALREADY MARRIED')
            await ctx.send(f"{instigator.mention}, they're already married .-.")
            return

        # Neither are married, set up the proposal
        async with self.bot.database() as db:
            await db.add_event(instigator=instigator, target=target, event='PROPOSAL')
        await ctx.send(f"{target.mention}, do you accept {instigator.mention}'s proposal?")

        # Make the check
        def check(message):
            '''
            The check to make sure that the user is giving a valid yes/no
            when provided with a proposal
            '''
            
            if message.author.id != target.id:
                return False
            c = message.content.casefold()
            yes = self.proposal_yes.search(c)
            no = self.proposal_no.search(c)
            if any([yes, no]):
                return 'YES' if yes else 'NO'
            return False

        # Wait for a response
        try:
            m = await self.bot.wait_for('message', check=check, timeout=60.0)
        except TimeoutError as e:
            async with self.bot.database() as db:
                await db.add_event(instigator=target, target=instigator, event='TIMEOUT')
            await ctx.send("The proposal has timed out. Try again when they're online!")
            return

        # Valid response recieved, see what their answer was
        response = check(m)
        if response == 'NO':
            async with self.bot.database() as db:
                await db.add_event(instigator=target, target=instigator, event='I DONT')
            await ctx.send("That's fair. The marriage has been called off.")
            return
        elif response == 'YES':
            async with self.bot.database() as db:
                await db.add_event(instigator=target, target=instigator, event='I DO')
                await db.marry(instigator, target)
            await ctx.send(f"{instigator.mention}, {target.mention}, I now pronounce you married.")
            return


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
