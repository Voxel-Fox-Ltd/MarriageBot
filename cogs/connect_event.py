from datetime import datetime as dt

import discord

from cogs import utils


class ConnectEvent(utils.Cog):

    @utils.Cog.listener()
    async def on_shard_connect(self, shard_id:int):
        """Ping a given webhook when the shard ID is connected"""

        if self.bot.config.get("event_webhook_url"):
            webhook = discord.Webhook.from_url(
                self.bot.config['event_webhook_url'],
                adapter=discord.AsyncWebhookAdapter(self.bot.session)
            )
            await webhook.send(
                f"Shard connect event just pinged for shard ID `{shard_id}` - {dt.utcnow().strftime('%X.%f')}",
                username=f"{self.bot.user.name} - Shard Connect"
            )
            self.logger.info(f"Sent webhook for on_shard_connect event in shard `{shard_id}`")

    @utils.Cog.listener()
    async def on_shard_ready(self, shard_id:int):
        """Ping a given webhook when the shard ID becomes ready"""

        if self.bot.config.get("event_webhook_url"):
            webhook = discord.Webhook.from_url(
                self.bot.config['event_webhook_url'],
                adapter=discord.AsyncWebhookAdapter(self.bot.session)
            )
            await webhook.send(
                f"Shard ready event just pinged for shard ID `{shard_id}` - {dt.utcnow().strftime('%X.%f')}",
                username=f"{self.bot.user.name} - Shard Ready"
            )
            self.logger.info(f"Sent webhook for on_shard_ready event in shard `{shard_id}`")

    @utils.Cog.listener()
    async def on_ready(self):
        """Ping a given webhook when the bot becomes ready"""

        if self.bot.config.get("event_webhook_url"):
            webhook = discord.Webhook.from_url(
                self.bot.config['event_webhook_url'],
                adapter=discord.AsyncWebhookAdapter(self.bot.session)
            )
            await webhook.send(
                f"Bot ready event just pinged for instance with shards `{self.bot.shard_ids}` - {dt.utcnow().strftime('%X.%f')}",
                username=f"{self.bot.user.name} - Ready"
            )
            self.logger.info("Sent webhook for on_ready event")

    @utils.Cog.listener()
    async def on_shard_disconnect(self, shard_id:int):
        """Ping a given webhook when the shard ID is disconnected"""

        if self.bot.config.get("event_webhook_url"):
            webhook = discord.Webhook.from_url(
                self.bot.config['event_webhook_url'],
                adapter=discord.AsyncWebhookAdapter(self.bot.session)
            )
            await webhook.send(
                f"Shard disconnect event just pinged for shard ID `{shard_id}` - {dt.utcnow().strftime('%X.%f')}",
                username=f"{self.bot.user.name} - Shard Disconnect"
            )
            self.logger.info(f"Sent webhook for on_shard_disconnect event in shard `{shard_id}`")

    @utils.Cog.listener()
    async def on_disconnect(self):
        """Ping a given webhook when the bot is disconnected"""

        if self.bot.config.get("event_webhook_url"):
            webhook = discord.Webhook.from_url(
                self.bot.config['event_webhook_url'],
                adapter=discord.AsyncWebhookAdapter(self.bot.session)
            )
            await webhook.send(
                f"Bot disconnect event just pinged for instance with shards `{self.bot.shard_ids}` - {dt.utcnow().strftime('%X.%f')}",
                username=f"{self.bot.user.name} - Disconnect"
            )
            self.logger.info("Sent webhook for on_disconnect event")


def setup(bot:utils.Bot):
    x = ConnectEvent(bot)
    bot.add_cog(x)
