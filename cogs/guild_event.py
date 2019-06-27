from datetime import datetime

from discord import Guild, Embed

from cogs.utils.custom_bot import CustomBot
from cogs.utils.family_tree.family_tree_member import FamilyTreeMember
from cogs.utils.custom_cog import Cog


class GuildEvent(Cog):

    def __init__(self, bot:CustomBot):
        super().__init__(self.__class__.__name__)
        self.bot = bot


    @property
    def event_log_channel(self):
        channel_id = self.bot.config['event_log_channel']
        channel = self.bot.get_channel(channel_id)
        return channel    


    @Cog.listener()
    async def on_guild_join(self, guild:Guild):
        '''
        When the client is added to a new guild
        '''

        if len(self.bot.guilds) % 5 == 0:
            await self.bot.post_guild_count()


    @Cog.listener()
    async def on_guild_remove(self, guild:Guild):
        '''
        When the client is removed from a guild
        '''

        if len(self.bot.guilds) % 5 == 0:
            await self.bot.post_guild_count()


def setup(bot:CustomBot):
    x = GuildEvent(bot)
    bot.add_cog(x)
