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
from cogs.utils.acceptance_check import AcceptanceCheck


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
        if ctx.original_author_id in self.bot.config['owners'] and not isinstance(error, CommandOnCooldown):
            text = f'```py\n{error}```'
            await ctx.send(text)
            raise error

        # Missing argument
        if isinstance(error, MissingRequiredArgument):
            await ctx.send("You need to specify a person for this command to work properly.")
            return

        # Cooldown
        elif isinstance(error, CommandOnCooldown):
            if ctx.original_author_id in self.bot.config['owners']:
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

        text = f"*You hug yourself... and start crying.*" if user == ctx.author else f"*Hugs {user.mention}*"
        await ctx.send(text)


    @command()
    @bot_is_ready()
    @cooldown(1, 5, BucketType.user)
    async def kiss(self, ctx:Context, user:Member):
        '''
        Kisses a mentioned user
        '''

        # Check if they're themself
        if user == ctx.author:
            await ctx.send(f"How would you even manage to do that?")
            return

        # Check if they're related
        x = FamilyTreeMember.get(ctx.author.id)
        y = FamilyTreeMember.get(user.id)
        async with ctx.channel.typing():
            relationship = x.get_relation(y)

        # Generate responses
        if relationship == None or relationship.casefold() == 'partner':
            responses = [
                f"*Kisses {user.mention}*"
            ]
        else:
            responses = [
                f"Woah woah, you two are family!",
                f"Incest is wincest, I guess.",
                f"You two are related but go off I guess.",
            ]
    
        # Boop an output
        await ctx.send(choice(responses))


    @command()
    @cooldown(1, 5, BucketType.user)
    async def slap(self, ctx:Context, user:Member):
        '''
        Slaps a mentioned user
        '''

        text = f"*You slapped yourself... for some reason.*" if user == ctx.author else f"*Slaps {user.mention}*"
        await ctx.send(text)


    @command()
    @cooldown(1, 5, BucketType.user)
    async def punch(self, ctx:Context, user:Member):
        '''
        Punches a mentioned user
        '''
        
        text = "*You punched yourself... for some reason.*" if user == ctx.author else f"*Punches {user.mention} right in the nose*"
        await ctx.send(text)


    @command()
    @cooldown(1, 5, BucketType.user)
    async def cookie(self, ctx:Context, user:Member):
        '''
        Gives a cookie to a mentioned user
        '''

        text = "*You gave yourself a cookie.*" if user == ctx.author else f"*Gives {user.mention} a cookie*"
        await ctx.send(text)


    @command()
    @cooldown(1, 5, BucketType.user) 
    async def poke(self, ctx:Context, user:Member):
        '''Pokes a given user'''

        text = "You poke yourself." if user == ctx.author else f"*Pokes {user.mention}.*"
        await ctx.send(text)
        
        
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
                f"No.",
            ]
        else:
            responses = [
                f"You stab {user.mention}.",
                f"{user.mention} has been stabbed.",
                f"*stabs {user.mention}.*",
                f"Looks like you don't have a knife, oops!"
            ]
        await ctx.send(choice(responses))


    @command(hidden=True, aliases=['murder'])
    async def kill(self, ctx:Context, user:Member=None):
        '''
        Do you really want to kill a person?
        '''
        
        responses = [
            "That would violate at least one of the laws of robotics.",
            "I am a text-based bot. I cannot kill.",
            "Unfortunately, murder isn't supported in this version of MarriageBot.",
            "Haha good joke there, but I'd never kill a person! >.>",
            "To my knowledge, you can't kill via the internet. Let me know when that changes.",
            "I am designed to bring people together, not murder them.",
        ]
        await ctx.send(choice(responses))


    @command(aliases=['vore'], hidden=True)
    async def eat(self, ctx:Context, user:Member=None):
        '''Eats a person OwO'''

        responses = [
            f"You swallowed {user.mention}... through the wrong hole.",
            f"You've eaten {user.mention}. Gross.",
            f"Are you into this or something? You've eaten {user.mention}.",
            f"I guess lunch wasnt good enough. You eat {user.mention}.",
            f"You insert {user.mention} into your mouth and proceed to digest them.",
        ]
        await ctx.send(choice(responses))


    @command(hidden=True)
    async def sleep(self, ctx:Context):
        '''Todd Howard strikes once more'''

        await ctx.send("You sleep for a while and when you wake up you're in a cart with your hands bound. A man says \"Hey, you. You're finally awake. You were trying to cross the border, right?\"")


    @command(aliases=['intercourse', 'fuck', 'smash'])
    @bot_is_ready()
    @cooldown(1, 5, BucketType.user)
    async def copulate(self, ctx:Context, user:Member):
        '''
        Lets you heck someone
        '''

        # Check for NSFW channel
        if not ctx.channel.is_nsfw():
            await ctx.send("This command can't be run in a non-NSFW channel.")
            return

        # Check for the most common catches
        text_processor = CopulateRandomText(self.bot)
        text = text_processor.process(ctx.author, user)
        if text:
            await ctx.send(text) 
            return

        # Check if they are related
        x = FamilyTreeMember.get(ctx.author.id)
        y = FamilyTreeMember.get(user.id)
        async with ctx.channel.typing():
            relationship = x.get_relation(y)
        if relationship == None or relationship.casefold() == 'partner':
            pass 
        elif not self.bot.allows_incest(ctx.guild.id):
            pass
        else:
            await ctx.send(text_processor.target_is_relation(ctx.author, user, relationship))
            return

        # Ping out a message for them
        await ctx.send(text_processor.valid_target(ctx.author, user))    

        # Wait for a response
        try:
            check = AcceptanceCheck(user.id, ctx.channel.id).check
            m = await self.bot.wait_for('message', check=check, timeout=60.0)
            response = check(m)
        except AsyncTimeoutError as e:
            await ctx.send(text_processor.proposal_timed_out(ctx.author, user), ignore_error=True)
            return

        # Process response
        if response == "NO":
            await ctx.send(text_processor.request_denied(ctx.author, user))
            return
        await ctx.send(text_processor.request_accepted(ctx.author, user))


def setup(bot:CustomBot):
    x = Simulation(bot)
    bot.add_cog(x)
