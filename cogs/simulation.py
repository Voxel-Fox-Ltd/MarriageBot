from re import compile
from random import choice
from asyncio import TimeoutError as AsyncTimeoutError

from discord import Member
from discord.ext.commands import command, Context, Cog, cooldown
from discord.ext.commands import MissingRequiredArgument, CommandOnCooldown, BadArgument
from discord.ext.commands.cooldowns import BucketType

from cogs.utils.custom_bot import CustomBot
from cogs.utils.family_tree.family_tree_member import FamilyTreeMember


class Simulation(Cog):


    def __init__(self, bot:CustomBot):
        self.bot = bot
        self.proposal_yes = compile(r"(i do)|(yes)|(of course)|(definitely)|(absolutely)|(yeah)|(yea)|(sure)")
        self.proposal_no = compile(r"(i don't)|(i dont)|(no)|(to think)|(i'm sorry)|(im sorry)")


    async def cog_command_error(self, ctx:Context, error):
        '''
        Local error handler for the cog
        '''

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


    @command()
    @cooldown(1, 5, BucketType.user)
    async def feed(self, ctx:Context, user:Member):
        '''
        Feeds a mentioned user
        '''

        if user == ctx.author:
            responses = [
                f"You feed yourself candy",
                f"You have been fed",
                f"You feed yourself",
                f"You feed yourself some chicken",
                f"You fed yourself too much.",
            ]
        else:
            responses = [
                f"*Feeds {user.mention} some candy.*",
                f"{user.mention} has been fed.",
                f"You feed {user.mention}.",
                f"*Feeds {user.mention} some chicken.",
                f"You feed {user.mention} too much.",
            ]
        await ctx.send(choice(responses))


    @command()
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
    async def snuggle(self, ctx:Context, user:Member):
        '''
        Snuggles a mentioned user
        '''

        if user == ctx.author:
            await ctx.send(f"*You snuggle yourself... and start crying.*")
            return

        await ctx.send(f"*Snuggles {user.mention}*")


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

        
    @command(aliases=['intercourse', 'fuck', 'smash'])
    @cooldown(1, 5, BucketType.user)
    async def copulate(self, ctx:Context, user:Member):
        '''
        Lets you heck someone
        '''

        if not ctx.channel.is_nsfw():
            await ctx.send("This command can't be run in a non-NSFW channel.")
            return
        
        if user == ctx.author:
            await ctx.send(self.bot.get_cog('CopulateRandomText').proposing_to_themselves(ctx.author, user))
            return

        # Check for a bot
        if user.id == self.bot.user.id:
            await ctx.send(self.bot.get_cog('CopulateRandomText').target_is_me(ctx.author, user))
            return
        elif user.bot:
            await ctx.send(self.bot.get_cog('CopulateRandomText').target_is_bot(ctx.author, user))
            return 

        #Check if they are related
        x = FamilyTreeMember.get(ctx.author.id)
        y = FamilyTreeMember.get(user.id)
        relationship = x.get_relation(y)
        if relationship == None or relationship.casefold() == 'partner':
            pass 
        else:
            await ctx.send(self.bot.get_cog('CopulateRandomText').target_is_relation(ctx.author, user, relationship))
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
            await ctx.send(self.bot.get_cog('CopulateRandomText').valid_proposal(ctx.author, user))
            m = await self.bot.wait_for('message', check=check, timeout=60.0)
            response = check(m)
        except AsyncTimeoutError as e:
            try:
                await ctx.send(self.bot.get_cog('CopulateRandomText').proposal_timed_out(ctx.author, user))
            except Exception as e:
                # If the bot was kicked, or access revoked, for example.
                pass
            return

        if response == "NO":
            await ctx.send(self.bot.get_cog('CopulateRandomText').declining_valid_proposal(ctx.author, user))
            return

        await ctx.send(self.bot.get_cog('CopulateRandomText').valid_target(ctx.author, user))


def setup(bot:CustomBot):
    x = Simulation(bot)
    bot.add_cog(x)
