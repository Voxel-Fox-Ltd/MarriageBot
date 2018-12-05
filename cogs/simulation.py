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

        await ctx.send(f"*Feeds {member} some candy*")


    @command()
    @cooldown(1, 5, BucketType.user)
    async def hug(self, ctx:Context, member:Member):
        '''
        Hugs a mentioned user
        '''

        await ctx.send(f"*Hugs {member}*")


    @command()
    @cooldown(1, 5, BucketType.user)
    async def kiss(self, ctx:Context, member:Member):
        '''
        Kisses a mentioned user
        '''

        await ctx.send(f"*Kisses {member}*")


    @command()
    @cooldown(1, 5, BucketType.user)
    async def snuggle(self, ctx:Context, member:Member):
        '''
        Snuggles a mentioned user
        '''

        await ctx.send(f"*Snuggles {member}*")


    @command()
    @cooldown(1, 5, BucketType.user)
    async def slap(self, ctx:Context, member:Member):
        '''
        Slaps a mentioned user
        '''

        await ctx.send(f"*Slaps {member}*")


    @command()
    @cooldown(1, 5, BucketType.user)
    async def punch(self, ctx:Context, member:Member):
        '''
        Punches a mentioned user
        '''

        await ctx.send(f"*Punches {member} right in the nose*")


def setup(bot:CustomBot):
    x = Simulation(bot)
    bot.add_cog(x)
