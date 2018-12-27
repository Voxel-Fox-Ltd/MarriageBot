from re import compile
from random import choice
from asyncio import TimeoutError

from discord import Member
from discord.ext.commands import command, Context, cooldown
from discord.ext.commands.cooldowns import BucketType

from cogs.utils.custom_bot import CustomBot
from cogs.utils.family_tree.family_tree_member import FamilyTreeMember


class Simulation(object):


    def __init__(self, bot:CustomBot):
        self.bot = bot
        self.proposal_yes = compile(r"(i do)|(yes)|(of course)|(definitely)|(absolutely)|(yeah)|(yea)|(sure)")
        self.proposal_no = compile(r"(i don't)|(i dont)|(no)|(to think)|(i'm sorry)|(im sorry)")


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
                f"*Feeds {user} some candy.*",
                f"{user} has been fed.",
                f"You feed {user}.",
                f"*Feeds {user} some chicken.",
                f"You feed {user} too much.",
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

        await ctx.send(f"*Hugs {user}*")


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
        
        relationship = x.get_relationship(y)
        if relationship = None:
        await ctx.send(f"*Kisses {user}*")
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

        await ctx.send(f"*Snuggles {user}*")


    @command()
    @cooldown(1, 5, BucketType.user)
    async def slap(self, ctx:Context, user:Member):
        '''
        Slaps a mentioned user
        '''

        if user == ctx.author:
            await ctx.send(f"*You slapped yourself... for some reason.*")
            return

        await ctx.send(f"*Slaps {user}*")


    @command()
    @cooldown(1, 5, BucketType.user)
    async def punch(self, ctx:Context, user:Member):
        '''
        Punches a mentioned user
        '''
        
        if user == ctx.author:
            await ctx.send(f"*You punched yourself... for some reason.*")
            return


        await ctx.send(f"*Punches {user} right in the nose*")


    @command(aliases=['intercourse', 'fuck', 'smash'])
    @cooldown(1, 5, BucketType.user)
    async def copulate(self, ctx:Context, user:Member):
        '''
        Lets you heck someone
        '''
        
        if user == ctx.author:
            await ctx.send(f"Not on my Christian Minecraft server.")
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

        x = await ctx.send(f"Hey, {user.mention}, do you wanna?")

        # Wait for a response
        try:
            if user.bot:
                raise KeyError
            m = await self.bot.wait_for('message', check=check, timeout=60.0)
            response = check(m)
        except TimeoutError as e:
            try:
                responses = [
                    f"Looks like the request timed out, {ctx.author.mention}!",
                    f"Looks like they fell asleep, {ctx.author.mention} .-.",
                ]
                await ctx.send(choice(responses))
                return
            except Exception as e:
                # If the bot was kicked, or access revoked, for example.
                pass
            return
        except KeyError as e:
            response = 'YES'

        if response == "NO":
            await ctx.send(f"Looks like they don't wanna smash, {ctx.author.mention}!")
            return

        responses = [
            f"{ctx.author.mention} and {user.mention} got frisky~",
            f"{ctx.author.mention} and {user.mention} spent some alone time together ~~wink wonk~~ ",
            f"{ctx.author.mention} and {user.mention} made sexy time together ;3",
            f"{ctx.author.mention} and {user.mention} attempted to make babies",
            f"{ctx.author.mention} and {user.mention} tried to have relations but couldn't find the hole",
            f"{ctx.author.mention} and {user.mention} went into the wrong hole",
            f"{ctx.author.mention} and {user.mention} tried your hardest, but {user.mention} came too early .-.",
            f"{ctx.author.mention} and {user.mention} slobbed each other's knobs",
            f"{ctx.author.mention} and {user.mention} had some frisky time in the pool and your doodoo got stuck because of pressure",
            f"{ctx.author.mention} and {user.mention} had sex and you've contracted an STI. uh oh!",
            f"{ctx.author.mention} and {user.mention} had sex but you finished early and now it's just a tad awkward.",
            f"Jesus saw what {ctx.author.mention} and {user.mention} did.",
            f"{ctx.author.mention} and {user.mention} did a lot of screaming"
            f"{ctx.author.mention} and {user.mention} had sex and pulled a muscle. No more hanky panky for a while!",
        ]

        await ctx.send(choice(responses))


def setup(bot:CustomBot):
    x = Simulation(bot)
    bot.add_cog(x)
