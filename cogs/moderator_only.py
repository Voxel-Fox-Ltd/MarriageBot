from discord import User
from discord.ext.commands import command, Context, cooldown
from discord.ext.commands.cooldowns import BucketType

from cogs.utils.custom_bot import CustomBot


class ModeratorOnly(object):

    def __init__(self, bot:CustomBot):
        self.bot = bot 


    def __local_check(self, ctx:Context):
        if ctx.author.id in self.bot.config['owners']:
            return True
        elif ctx.guild == None:
            return False
        if self.bot.config['bot_admin_role'] in [i.id for i in ctx.author.roles]:
            return True
        return False

    @command()
    async def uncache(self, ctx:Context, user:User):
        '''
        Removes a user from the propsal cache.
        '''

        x = self.bot.proposal_cache.remove(user.id)
        if x:
            await ctx.send("Removed from proposal cache.")
        else:
            await ctx.send("The user wasn't even in the cache but go off I guess.")
        


def setup(bot:CustomBot):
    x = ModeratorOnly(bot)
    bot.add_cog(x)
    
