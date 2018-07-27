from discord import Guild
from cogs.utils.custom_bot import CustomBot


class GuildEvent(object):

    def __init__(self, bot:CustomBot):
        self.bot = bot


    @property
    def log_channel(self):
        channel_id = self.bot.config['log_channel']
        channel = self.bot.get_channel(channel_id)
        return channel    


    async def on_guild_join(self, guild:Guild):
        '''
        When the client is added to a new guild
        '''

        await self.log_channel.send(
            f"**Added to new guild** (#{len(self.bot.guilds)}\n"
            f"__Name__: {gulid.name}\n"
            f"__ID__: {guild.id}\n"
            f"__Member Count__: {len(guld.members)}\n"
            )


    async def on_guild_remove(self, guild:Guild):
        '''
        When the client is removed from a guild
        '''

        await self.log_channel.send(
            f"**Removed from guild** (#{len(self.bot.guilds)}\n"
            f"__Name__: {gulid.name}\n"
            f"__ID__: {guild.id}\n"
            f"__Member Count__: {len(guld.members)}\n"
            )


def setup(bot:CustomBot):
    x = GuildEvent(bot)
    bot.add_cog(x)
