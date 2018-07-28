from discord.ext.commands import command, Context
from cogs.utils.custom_bot import CustomBot 


class Misc(object):

    def __init__(self, bot:CustomBot):
        self.bot = bot 


    @command(aliases=['git', 'code'])
    async def github(self, ctx:Context):
        '''
        Gives you a link to the bot's code repository
        '''

        await ctx.send(f"<{self.bot.config['github']}>")


    @command()
    async def patreon(self, ctx:Context):
        '''
        Gives you the creator's Patreon link
        '''

        await ctx.send(f"<{self.bot.config['patreon']}>")


    @command()
    async def invite(self, ctx:Context):
        '''
        Gives you an invite link for the bot
        '''

        await ctx.send(
            f"<https://discordapp.com/oauth2/authorize?client_id={self.bot.user.id}&scope=bot&permissions=35840>"
        )


    @command(aliases=['guild', 'support'])
    async def server(self, ctx:Context):
        '''
        Gives you a server invite link
        '''

        await ctx.send(self.bot.config['guild'])


def setup(bot:CustomBot):
    x = Misc(bot)
    bot.add_cog(x)
