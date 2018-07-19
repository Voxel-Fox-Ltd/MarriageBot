from re import compile
from asyncio import TimeoutError
from discord import Member
from discord.ext.commands import command, Context
from cogs.utils.custom_bot import CustomBot


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

        # Adoption cache
        self.cache = []


    @command()
    async def parent(self, ctx:Context, parent:Member):
        '''
        Picks a user that you want to be your parent
        '''

        instigator = ctx.author
        target = parent  # Just so "target" didn't show up in the help message

        # See if either user is already being proposed to
        if instigator.id in self.cache:
            await ctx.send("You can only make one adoption request at a time .-.")
            return
        elif target.id in self.cache:
            await ctx.send("That person has already been asked to adopt. Please wait.")
            return

        # Manage exclusions
        if target.id == self.bot.user.id:
            await ctx.send("I'm flattered but no, sweetheart 😘")
            return
        elif target.bot or instigator.bot:
            await ctx.send("Robots don't make particularly good parents.")
            return
        elif instigator.id == target.id:
            await ctx.send("Are you serious.")
            return

        # See if they already have a parent
        async with self.bot.database() as db:
            parentage = await db.get_parent(instigator)
            children = await db.get_children(instigator)
            marriage = await db.get_marriage(instigator)
        if parentage:
            await ctx.send("Sorry, but you already have a parent :/")
            return
        elif target.id in children:
            await ctx.send("That is your child. You can't make your child your parent.")
            return
        elif target.id in [marriage[0]['user_id'], marriage[0]['partner_id']]:
            await ctx.send("Sorry to say this but you can't marry your spouse.")
            return

        # Make sure the user knows
        m = await ctx.send(f"Just to make sure, {instigator.mention}, you should know you can't change your parent after you do this, and you can only have one. Do you want to continue?")
        await m.add_reaction('👌')
        await m.add_reaction('👎')
        try:
            r, u = await self.bot.wait_for('reaction_add', check=lambda r, u: u.id == instigator.id and r.emoji in ['👌', '👎'], timeout=60.0)
            if r == '👎':
                await ctx.send("Well, that's your choice.")
                return
        except TimeoutError as e:
            await ctx.send("Well, the timeout has spoken.")
            return

        # No parent, send request
        async with self.bot.database() as db:
            await db.add_event(instigator=instigator, target=target, event='PARENT REQUEST')
        await ctx.send(f"{target.mention}, do you want to be {instigator.mention}'s parent?")
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
            await ctx.send(f"{instigator.mention}, your parent request has timed out. Try again when they're online!")
            self.cache.remove(instigator.id)
            self.cache.remove(target.id)
            return

        # Valid response recieved, see what their answer was
        response = check(m)
        if response == 'NO':
            async with self.bot.database() as db:
                await db.add_event(instigator=target, target=instigator, event='DECLINE ADOPTION')
            await ctx.send("No adoption today, it seems..")
        elif response == 'YES':
            async with self.bot.database() as db:
                await db.add_event(instigator=target, target=instigator, event='ACCEPT ADOPTION')
                await db('INSERT INTO parents (child_id, parent_id) VALUES ($1, $2)', instigator.id, target.id)
            await ctx.send(f"{instigator.mention}, your new parent is {target.mention} c:")

        self.cache.remove(instigator.id)
        self.cache.remove(target.id)


def setup(bot:CustomBot):
    x = Parentage(bot)
    bot.add_cog(x)
