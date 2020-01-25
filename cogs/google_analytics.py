import discord

from cogs import utils


class GoogleAnalytics(utils.Cog):

    def __init__(self, bot:utils.Bot):
        super().__init__(bot)
        self.url = 'https://www.google-analytics.com/collect'
        self.base_params = {
            "v": "1",
            "t": "pageview",
            "aip": "1",
            "tid": self.bot.config['google_analytics']['tracking_id'],
            "an": self.bot.config['google_analytics']['app_name'],
            "dh": self.bot.config['google_analytics']['document_host'],
        }

        """
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
        """

    @utils.Cog.listener()
    async def on_command(self, ctx:utils.Context):
        """Logs a command that's been sent"""

        params = self.base_params.copy()
        params.update({
            "dp": f"/commands/{ctx.command.name}",
            "cid": f"{ctx.author.id}",
            "cs": f"{ctx.guild.id}" if ctx.guild is not None else "PRIVATE_MESSAGE",
            "dt": ctx.command.name,
        })
        async with self.bot.session.get(self.url, params=params) as r:
            pass

    @utils.Cog.listener()
    async def on_guild_join(self, guild:discord.Guild):
        """Logs when added to a guild"""

        params = self.base_params.copy()
        params.update({
            "dp": f"/events/GUILD_ADD",
            "cid": f"{guild.id}",
            "cs": f"{guild.id}",
            "dt": "GUILD_ADD",
        })
        async with self.bot.session.get(self.url, params=params) as r:
            pass

    @utils.Cog.listener()
    async def on_guild_remove(self, guild:discord.Guild):
        """Logs when a guild is removed from the client"""

        params = self.base_params.copy()
        params.update({
            "dp": f"/events/GUILD_REMOVE",
            "cid": f"{guild.id}",
            "cs": f"{guild.id}",
            "dt": "GUILD_REMOVE",
        })
        async with self.bot.session.get(self.url, params=params) as r:
            pass


def setup(bot:utils.Bot):
    x = GoogleAnalytics(bot)
    if '' in list(bot.config['google_analytics'].values()):
        x.log_handler.error("Google Analytics authorization not set in config - not loading cog.")
    else:
        bot.add_cog(x)
