import discord

from cogs import utils


class GuildCountPoster(utils.Cog):

    @utils.Cog.listener()
    async def on_guild_join(self, guild:discord.Guild):
        """Pinged when a client is added to a new guild, updating the guild count"""

        self.log_handler.info(f"Added to guild {guild.name} ({guild.id})")
        if len(self.bot.guilds) % 5 == 0:
            await self.bot.post_guild_count()

    @utils.Cog.listener()
    async def on_guild_remove(self, guild:discord.Guild):
        """Pinged when a client is removed from a guild, updating the guild count"""

        self.log_handler.info(f"Removed from guild {guild.name} ({guild.id})")
        if len(self.bot.guilds) % 5 == 0:
            await self.bot.post_guild_count()


def setup(bot:utils.CustomBot):
    x = GuildCountPoster(bot)
    bot.add_cog(x)
