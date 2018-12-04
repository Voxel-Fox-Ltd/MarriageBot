from discord import Member
from discord.ext.commands import command, Context, cooldown
from discord.ext.commands.cooldowns import BucketType

from cogs.utils.custom_bot import CustomBot


class Simulation(object):


    def __init__(self, bot:CustomBot):
        self.bot = bot


    @command()
    @cooldown(1, 5, BucketType.user)
    async def feed(self, member:Member):
        '''
        Feeds a mentioned user
        '''

        await ctx.send(f"*Feeds {member} some candy")


def setup(bot:CustomBot):
    x = Simulation(bot)
    bot.add_cog(x)
