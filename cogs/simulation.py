from re import compile
from random import choice
from asyncio import TimeoutError as AsyncTimeoutError

from discord import Member
from discord.ext.commands import command, Context, cooldown
from discord.ext.commands import MissingRequiredArgument, CommandOnCooldown, BadArgument
from discord.ext.commands.cooldowns import BucketType

from cogs.utils.custom_bot import CustomBot
from cogs.utils.family_tree.family_tree_member import FamilyTreeMember
from cogs.utils.custom_cog import Cog
from cogs.utils.random_text.copulate import CopulateRandomText
from cogs.utils.checks.bot_is_ready import bot_is_ready, BotNotReady


class Simulation(Cog):


    def __init__(self, bot:CustomBot):
        super().__init__(self.__class__.__name__)
        self.bot = bot
        self.proposal_yes = compile(r"(i do)|(yes)|(of course)|(definitely)|(absolutely)|(yeah)|(yea)|(sure)|(accept)")
        self.proposal_no = compile(r"(i don't)|(i dont)|(no)|(to think)|(i'm sorry)|(im sorry)")


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
    
        # Argument conversion error
        elif isinstance(error, BadArgument):
            argument_text = self.bot.bad_argument.search(str(error)).group(2)
            await ctx.send(f"User `{argument_text}` could not be found.")
            return

        # Bot ready
        elif isinstance(error, BotNotReady):
            await ctx.send("The bot isn't ready to start processing that command yet - please wait.")
            return


    @command(enabled=False)
    @cooldown(1, 5, BucketType.user)
    async def feed(self, ctx:Context, user:Member):
        '''
        Feeds a mentioned user
        '''

        user = user or ctx.author
        responses = [
            
        ]            
        await ctx.send(choice(responses))


    @command(aliases=['snuggle'])
    @cooldown(1, 5, BucketType.user)
    async def hug(self, ctx:Context, user:Member):
        '''
        Hugs a mentioned user
        '''

        if user == ctx.author:
            await ctx.send(f"*You hug yourself... and start crying.*")
            return

        await ctx.send(f"*Hugs {user.mention}*")


    @command()
    @bot_is_ready()
    @cooldown(1, 5, BucketType.user)
    async def kiss(self, ctx:Context, user:Member):
        '''
        Kisses a mentioned user
        '''

        if user == ctx.author:
            await ctx.send(f"How does one even manage to do that?")
            return

        #Check if they are related
        x = FamilyTreeMember.get(ctx.author.id)
        y = FamilyTreeMember.get(user.id)
        relationship = x.get_relation(y)
        if relationship == None or relationship.casefold() == 'partner':
            await ctx.send(f"*Kisses {user.mention}*")
            return
        else:
            responses = [
                f"Well you two lovebirds may be related but... I'll allow it :smirk:",
                f"Woah woah, you two are family!",
                f"Incest is wincest, I guess.",
                f"You two are related but go off I guess.",
            ]
        await ctx.send(choice(responses))


    @command()
    @cooldown(1, 5, BucketType.user)
    async def slap(self, ctx:Context, user:Member):
        '''
        Slaps a mentioned user
        '''

        if user == ctx.author:
            await ctx.send(f"*You slapped yourself... for some reason.*")
            return
        await ctx.send(f"*Slaps {user.mention}*")


    @command()
    @cooldown(1, 5, BucketType.user)
    async def punch(self, ctx:Context, user:Member):
        '''
        Punches a mentioned user
        '''
        
        if user == ctx.author:
            await ctx.send(f"*You punched yourself... for some reason.*")
            return
        await ctx.send(f"*Punches {user.mention} right in the nose*")


    @command()
    @cooldown(1, 5, BucketType.user)
    async def cookie(self, ctx:Context, user:Member):
        '''
        Gives a cookie to a mentioned user
        '''

        if user == ctx.author:
            await ctx.send(f"*You gave yourself a cookie.*")
            return


        await ctx.send(f"*Gives {user.mention} a cookie*")
        
        
    @command()
    @cooldown(1, 5, BucketType.user)
    async def stab(self, ctx:Context, user:Member):
        '''
        Stabs a mentioned user
        '''

        if user == ctx.author:
            responses = [
                f"You stab yourself.",
                f"Looks like you don't have a knife, oops!",
                f"No",
            ]
        else:
            responses = [
                f"You stab {user.mention}.",
                f"{user.mention} has been stabbed.",
                f"*stabs {user.mention}.*",
                f"Looks like you don't have a knife, oops!"
            ]
        await ctx.send(choice(responses))        


    @command(aliases=['intercourse', 'fuck', 'smash'])
    @bot_is_ready()
    @cooldown(1, 5, BucketType.user)
    async def copulate(self, ctx:Context, user:Member):
        '''
        Lets you heck someone
        '''

        if not ctx.channel.is_nsfw():
            await ctx.send("This command can't be run in a non-NSFW channel.")
            return

        text_processor = CopulateRandomText(self.bot)
        
        if user == ctx.author:
            await ctx.send(text_processor.proposing_to_themselves(ctx.author, user))
            return

        # Check for a bot
        if user.id == self.bot.user.id:
            await ctx.send(text_processor.target_is_me(ctx.author, user))
            return
        elif user.bot:
            await ctx.send(text_processor.target_is_bot(ctx.author, user))
            return 

        #Check if they are related
        x = FamilyTreeMember.get(ctx.author.id)
        y = FamilyTreeMember.get(user.id)
        relationship = x.get_relation(y)
        if relationship == None or relationship.casefold() == 'partner':
            pass 
        else:
            await ctx.send(text_processor.target_is_relation(ctx.author, user, relationship))
            return

        # Make the check
        def check(message):
            '''
            The check to make sure that the user is giving a valid yes/no
            when provided with a proposal
            '''
            
            if message.author.id != user.id:
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
            await ctx.send(text_processor.valid_proposal(ctx.author, user))
            m = await self.bot.wait_for('message', check=check, timeout=60.0)
            response = check(m)
        except AsyncTimeoutError as e:
            await ctx.send(text_processor.proposal_timed_out(ctx.author, user), ignore_error=True)
            return

        if response == "NO":
            await ctx.send(text_processor.declining_valid_proposal(ctx.author, user))
            return

        await ctx.send(text_processor.valid_target(ctx.author, user))


def setup(bot:CustomBot):
    x = Simulation(bot)
    bot.add_cog(x)
