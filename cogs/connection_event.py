from discord import Game
from discord.ext.tasks import loop

from cogs.utils.custom_bot import CustomBot
from cogs.utils.custom_cog import Cog


class ConnectionEvent(Cog):

    def __init__(self, bot:CustomBot):
        super().__init__(self.__class__.__name__)
        self.bot = bot 
        self.counter = 0


    def cog_unload(self):
        self.shard_ready_loop.cancel()


    @Cog.listener()
    async def on_shard_ready(self, shard_id:int):
        '''Update the presence when the shard becomes ready'''

        self.log_handler.info(f"`on_shard_ready` called for shard ID `{shard_id}`.")
        presence_text = self.bot.config['presence_text']
        game = Game(f"{presence_text} (shard {shard_id})".strip())
        await self.bot.change_presence(activity=game, shard_id=shard_id)


    @Cog.listener('on_message')
    async def shard_ready_loop(self, message):
        '''Check minutely if the bot is ready and update based on that'''

        self.counter += 1
        if self.counter % 100 == 0 and self.bot.is_ready():
            for i in self.bot.shard_ids:
                presence_text = self.bot.config['presence_text']
                game = Game(f"{presence_text} (shard {i})".strip())
                await self.bot.change_presence(activity=game, shard_id=i)


def setup(bot:CustomBot):
    x = ConnectionEvent(bot)
    bot.add_cog(x)
