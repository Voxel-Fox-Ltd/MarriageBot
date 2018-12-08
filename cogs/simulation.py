from discord import Member
from discord.ext.commands import command, Context, cooldown
from discord.ext.commands.cooldowns import BucketType

from cogs.utils.custom_bot import CustomBot


class Simulation(object):


    def __init__(self, bot:CustomBot):
        self.bot = bot


    @command()
    @cooldown(1, 5, BucketType.user)
    async def feed(self, ctx:Context, member:Member):
        '''
        Feeds a mentioned user
        '''

       if user == ctx.author:
       responses = [
            "You feed yourself candy",
            "You have been fed",
            "You feed yourself",
            "You feed yourself some chicken",
            "You fed yourself too much.",
        ]
        await ctx.send(choice(responses))
        return

        responses = [
            "*Feeds {member} some candy.*",
            "{member} has been fed.",
            "You feed {member}.",
            "*Feeds {member} some chicken.",
            "You feed {member} too much.",
        ]
        await ctx.send(choice(responses))

    @command()
    @cooldown(1, 5, BucketType.user)
    async def hug(self, ctx:Context, member:Member):
        '''
        Hugs a mentioned user
        '''

        if user == ctx.author:
            await ctx.send(f"*You hug yourself... and start crying.*")
            return

        await ctx.send(f"*Hugs {member}*")


    @command()
    @cooldown(1, 5, BucketType.user)
    async def kiss(self, ctx:Context, member:Member):
        '''
        Kisses a mentioned user
        '''
        if user == ctx.author:
            await ctx.send(f"How does one even manage to do that?")
            return

        await ctx.send(f"*Kisses {member}*")


    @command()
    @cooldown(1, 5, BucketType.user)
    async def snuggle(self, ctx:Context, member:Member):
        '''
        Snuggles a mentioned user
        '''
        if user == ctx.author:
            await ctx.send(f"*You snuggle yourself... and start crying.*")
            return

        await ctx.send(f"*Snuggles {member}*")


    @command()
    @cooldown(1, 5, BucketType.user)
    async def slap(self, ctx:Context, member:Member):
        '''
        Slaps a mentioned user
        '''
        if user == ctx.author:
            await ctx.send(f"*You slapped yourself... for some reason.*")
            return

        await ctx.send(f"*Slaps {member}*")


    @command()
    @cooldown(1, 5, BucketType.user)
    async def punch(self, ctx:Context, member:Member):
        '''
        Punches a mentioned user
        '''
        if user == ctx.author:
            await ctx.send(f"*You punched yourself... for some reason.*")
            return


        await ctx.send(f"*Punches {member} right in the nose*")


def setup(bot:CustomBot):
    x = Simulation(bot)
    bot.add_cog(x)
