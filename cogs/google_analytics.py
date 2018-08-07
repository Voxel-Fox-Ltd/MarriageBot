from random import randint
from aiohttp import ClientSession
from discord import Guild
from discord.ext.commands import Context, CommandNotFound
from cogs.utils.custom_bot import CustomBot


class GoogleAnalytics(object): 

    def __init__(self, bot:CustomBot):
        self.bot = bot
        self.session = ClientSession(loop=bot.loop)
        self.url = 'https://www.google-analytics.com/collect'
        self.base_params = {
            "v": "1",
            "t": "pageview",
            "aip": "1",
            "tid": self.bot.config['google_analytics']['tracking_id'],
            "an": self.bot.config['google_analytics']['app_name'],
        }


    def __unload(self):
        self.session.close()


    async def on_command(self, ctx:Context):
        '''
        Logs a command that's been sent
        '''

        params = self.base_params.copy()
        if ctx.guild:
            params.update({
                "dp": f"/commands/{ctx.command.name}",
                "uid": f"{ctx.author.id}",
                "cs": f"{ctx.guild.id}",
                "cm": f"{ctx.author.id}",
                "cd": ctx.command.name,
                "dt": ctx.command.name,
                "cc": ctx.message.content,
            })
        else:
            params.update({
                "dp": f"/commands/{ctx.command.name}",
                "uid": f"{ctx.author.id}",
                "cs": 'PRIVATE_MESSAGE',
                "cm": f"{ctx.author.id}",
                "cd": ctx.command.name,
                "dt": ctx.command.name,
                "cc": ctx.message.content,
            })
        async with self.session.get(self.url, params=params) as r:
            pass
            # print(r.url)


    async def on_guild_add(self, guild:Guild):
        '''
        Logs when added to a guild
        '''

        params = self.base_params.copy()
        params.update({
            "dp": f"/events/GUILD_ADD",
            "cid": f"{guild.id}",
            "cs": f"{guild.id}",
            "cd": "GUILD_ADD",
            "dt": "GUILD_ADD",
        })
        async with self.session.get(self.url, params=params) as r:
            pass


    async def on_guild_remove(self, guild:Guild):
        '''
        Logs when a guild is removed from the client
        '''

        params = self.base_params.copy()
        params.update({
            "dp": f"/events/GUILD_REMOVE",
            "cid": f"{guild.id}",
            "cs": f"{guild.id}",
            "cd": "GUILD_REMOVE",
            "dt": "GUILD_REMOVE",
        })
        async with self.session.get(self.url, params=params) as r:
            pass


def setup(bot:CustomBot):
    x = GoogleAnalytics(bot)
    bot.add_cog(x)
