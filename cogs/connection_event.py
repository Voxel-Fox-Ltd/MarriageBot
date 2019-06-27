from discord import Game

from cogs.utils.custom_bot import CustomBot
from cogs.utils.custom_cog import Cog


class ConnectionEvent(Cog):

    def __init__(self, bot:CustomBot):
        super().__init__(self.__class__.__name__)
        self.bot = bot 


    @Cog.listener()
    async def on_shard_ready(self, shard_id:int):
        self.log_handler.info(f"`on_shard_ready` called for shard ID `{shard_id}`.")
        presence_text = self.bot.config['presence_text']
        game = Game(f"{presence_text} (shard {shard_id})".strip())
        await self.bot.change_presence(activity=game, shard_id=shard_id)


def setup(bot:CustomBot):
    x = ConnectionEvent(bot)
    bot.add_cog(x)
