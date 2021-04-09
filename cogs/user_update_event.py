import discord

from cogs import utils


class UserUpdateEvent(utils.Cog):
    @utils.Cog.listener()
    async def on_user_update(self, before: discord.User, after: discord.User):
        """Caches a username change into the redis cache"""

        if before.name == after.name:
            return
        async with self.bot.redis() as re:
            await re.set(f"UserName-{after.id}", str(after))


def setup(bot: utils.Bot):
    x = UserUpdateEvent(bot)
    bot.add_cog(x)
