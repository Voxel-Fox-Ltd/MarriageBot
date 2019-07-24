from datetime import datetime

from discord import Guild, Embed

from cogs.utils.custom_bot import CustomBot
from cogs.utils.family_tree.family_tree_member import FamilyTreeMember
from cogs.utils.custom_cog import Cog


class GuildEvent(Cog):

    def __init__(self, bot:CustomBot):
        super().__init__(self.__class__.__name__)
        self.bot = bot 


    @Cog.listener()
    async def on_guild_join(self, guild:Guild):
        '''
        When the client is added to a new guild
        '''

        if self.bot.config['server_specific']:
            async with self.bot.database() as db:
                data = await db('SELECT guild_id FROM guild_specific_families WHERE guild_id=$1', guild.id)
                if not data:
                    self.log_handler.warn(f"Automatically left guild {guild.name} ({guild.id}) for non-subscription")
                    await guild.leave()
                    return
        self.log_handler.info(f"Added to guild {guild.name} ({guild.id})")

        if len(self.bot.guilds) % 5 == 0:
            await self.bot.post_guild_count()


    @Cog.listener()
    async def on_guild_remove(self, guild:Guild):
        '''
        When the client is removed from a guild
        '''

        self.log_handler.info(f"Removed from guild {guild.name} ({guild.id})")
        if len(self.bot.guilds) % 5 == 0:
            await self.bot.post_guild_count()


def setup(bot:CustomBot):
    x = GuildEvent(bot)
    bot.add_cog(x)
