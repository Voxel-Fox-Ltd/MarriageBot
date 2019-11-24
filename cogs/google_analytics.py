from random import randint

from aiohttp import ClientSession
from discord import Guild
from discord.ext.commands import Context, CommandNotFound

from cogs.utils.custom_bot import CustomBot
from cogs.utils.custom_cog import Cog


class GoogleAnalytics(Cog): 

    def __init__(self, bot:CustomBot):
        super().__init__(self.__class__.__name__)
        self.bot = bot
        self.url = 'https://www.google-analytics.com/collect'
        self.base_params = {
            "v": "1",
            "t": "pageview",
            "aip": "1",
            "tid": self.bot.config['google_analytics']['tracking_id'],
            "an": self.bot.config['google_analytics']['app_name'],
            "dh": self.bot.config['google_analytics']['document_host'],
        }

        '''
        v: version
        t: type (of hit)
        aip: anonymise IP
        tid: tracking ID
        an: application name
        dp: document path
        dh: document host
        uid: user ID
        cid: client ID
        cs: campaign source
        cm: campaign medium
        cd: screen name
        dt: document title
        cc: campaign content
        '''


    @Cog.listener()
    async def on_command(self, ctx:Context):
        '''
        Logs a command that's been sent
        '''

        params = self.base_params.copy()
        if ctx.guild:
            params.update({
                "dp": f"/commands/{ctx.command.name}",
                "cid": f"{ctx.author.id}",
                "cs": f"{ctx.guild.id}",
                # "cm": f"{ctx.author.id}",
                "dt": ctx.command.name,
                # "cc": ctx.message.content,
            })
        else:
            params.update({
                "dp": f"/commands/{ctx.command.name}",
                "cid": f"{ctx.author.id}",
                "cs": 'PRIVATE_MESSAGE',
                # "cm": f"{ctx.author.id}",
                "dt": ctx.command.name,
                # "cc": ctx.message.content,
            })
        async with self.bot.session.get(self.url, params=params) as r:
            pass
            # print(r.url)


    @Cog.listener()
    async def on_guild_join(self, guild:Guild):
        '''
        Logs when added to a guild
        '''

        params = self.base_params.copy()
        params.update({
            "dp": f"/events/GUILD_ADD",
            "cid": f"{guild.id}",
            "cs": f"{guild.id}",
            "dt": "GUILD_ADD",
        })
        async with self.bot.session.get(self.url, params=params) as r:
            pass


    @Cog.listener()
    async def on_guild_remove(self, guild:Guild):
        '''
        Logs when a guild is removed from the client
        '''

        params = self.base_params.copy()
        params.update({
            "dp": f"/events/GUILD_REMOVE",
            "cid": f"{guild.id}",
            "cs": f"{guild.id}",
            "dt": "GUILD_REMOVE",
        })
        async with self.bot.session.get(self.url, params=params) as r:
            pass


def setup(bot:CustomBot):
    x = GoogleAnalytics(bot)
    if '' in list(bot.config['google_analytics'].values()):
        x.log_handler.error("Google Analytics authorization not set in config - not loading cog.") 
    else:
        bot.add_cog(x)
