from discord.ext import tasks

from cogs import utils


class PresenceAutoUpdater(utils.Cog):

    def __init__(self, bot:utils.Bot):
        super().__init__(bot)
        self.shard_ready_loop.start()

    def cog_unload(self):
        self.shard_ready_loop.cancel()

    @utils.Cog.listener()
    async def on_shard_ready(self, shard_id:int):
        """Update the presence when the shard becomes ready"""

        self.logger.info(f"`on_shard_ready` called for shard ID `{shard_id}`.")
        await self.bot.set_default_presence(shard_id=shard_id)

    @tasks.loop(minutes=1)
    async def shard_ready_loop(self):
        """Checks if the shard is ready, and if it _is_ then it sets the presence as necessary"""

        if self.bot.is_ready():
            await self.bot.set_default_presence()


def setup(bot:utils.Bot):
    x = PresenceAutoUpdater(bot)
    bot.add_cog(x)
