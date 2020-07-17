import json

import discord
from discord.ext import tasks

from cogs import utils


class Analytics(utils.Cog):

    GOOGLE_ANALYTICS_URL = 'https://www.google-analytics.com/collect'

    """
    v   : version            : !1
    t   : type (of hit)      : !pageview
    aip : anonymise IP       : !true
    tid : tracking ID        : ?from config
    an  : application name   : ?from config
    dp  : document path      : command/event name
    dh  : document host      : ?from config
    uid : user ID            : Discord user ID
    cs  : campaign source    : guild ID
    cm  : campaign medium
    cd  : screen name
    dt  : document title     : command/event name
    cc  : campaign content
    dr  : document referrer  : !discord.com
    cd1 : custom dimension 1 : !timestamp
    cm1 : custom metric 1    : ISO-format timestamp
    """

    def __init__(self, bot):
        super().__init__(bot)
        self.post_guild_count.start()

    def cog_unload(self):
        self.post_guild_count.stop()

    @tasks.loop(minutes=30)
    async def post_guild_count(self):
        """Post the average guild count to DiscordBots.org"""

        # Only shard 0 can post
        if self.bot.shard_count and self.bot.shard_count > 1 and 0 not in self.bot.shard_ids:
            return

        # Only post if there's actually a DBL token set
        if not self.bot.config.get('topgg_token'):
            self.logger.warning("No DBL token has been provided")
            return

        url = f'https://top.gg/api/bots/{self.bot.user.id}/stats'
        data = {
            'server_count': int((len(self.bot.guilds) / len(self.bot.shard_ids)) * self.bot.shard_count),
            'shard_count': self.bot.shard_count,
            'shard_id': 0,
        }
        headers = {
            'Authorization': self.bot.config['topgg_token']
        }
        self.logger.info(f"Sending POST request to DBL with data {json.dumps(data)}")
        async with self.bot.session.post(url, json=data, headers=headers):
            pass

    @post_guild_count.before_loop
    async def before_post_guild_count(self):
        await self.bot.wait_until_ready()

    async def try_send_ga_data(self, data):
        """Post the cached data over to Google Analytics"""

        # See if we should bother doing it
        ga_data = self.bot.config.get('google_analytics')
        if not ga_data:
            return
        if '' in ga_data.values():
            return

        # Set up the params for us to use
        base_ga_params = {
            "v": "1",
            "t": "pageview",
            "aip": "1",
            "tid": ga_data['tracking_id'],
            "an": ga_data['app_name'],
            "dh": ga_data['document_host'],
            "dr": "discord.com",
        }
        data.update(base_ga_params)
        async with self.bot.session.get(self.GOOGLE_ANALYTICS_URL, params=data):
            pass

    @utils.Cog.listener()
    async def on_command(self, ctx:utils.Context):
        """Logs a command that's been sent"""

        params = {
            "dp": f"/commands/{ctx.command.name}",
            "cid": f"{ctx.author.id}",
            "cs": f"{ctx.guild.id}" if ctx.guild is not None else "PRIVATE_MESSAGE",
            "dt": ctx.command.name,
        }
        await self.try_send_ga_data(params)

    @utils.Cog.listener()
    async def on_guild_join(self, guild:discord.Guild):
        """Logs when added to a guild"""

        params = {
            "dp": "/events/GUILD_ADD",
            "cid": f"{guild.id}",
            "cs": f"{guild.id}",
            "dt": "GUILD_ADD",
        }
        await self.try_send_ga_data(params)

    @utils.Cog.listener()
    async def on_guild_remove(self, guild:discord.Guild):
        """Logs when a guild is removed from the client"""

        params = {
            "dp": "/events/GUILD_REMOVE",
            "cid": f"{guild.id}",
            "cs": f"{guild.id}",
            "dt": "GUILD_REMOVE",
        }
        await self.try_send_ga_data(params)


def setup(bot:utils.Bot):
    x = Analytics(bot)
    bot.add_cog(x)
