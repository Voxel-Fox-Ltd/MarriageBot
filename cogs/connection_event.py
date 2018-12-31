from discord import Game

from cogs.utils.custom_bot import CustomBot


class ConnectionEvent(object):

    def __init__(self, bot:CustomBot):
        self.bot = bot 


    @property
    def event_log_channel(self):
        channel_id = self.bot.config['event_log_channel']
        channel = self.bot.get_channel(channel_id)
        return channel


    # async def on_connect(self):
    #     await self.event_log_channel.send("`on_connect` called.")


    # async def on_ready(self):
    #     await self.event_log_channel.send("`on_ready` called.")


    async def on_shard_ready(self, shard_id:int):
        await self.event_log_channel.send(f"`on_shard_ready` called for shard ID `{shard_id}`.")
        presence_text = self.bot.config['presence_text']
        game = Game(f"{presence_text} (shard {shard_id})")
        await self.bot.change_presence(activity=game, shard_id=shard_id)


def setup(bot:CustomBot):
    x = ConnectionEvent(bot)
    bot.add_cog(x)
