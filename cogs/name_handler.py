import discord
import voxelbotutils as utils


class NameHandler(utils.Cog):
    """
    This cog mainly just update's people usernames as a way to avoid getting unnessacary m!cachename support requests
    """

    @utils.Cog.listener()
    async def on_message(self, message:discord.Message):
        """
        Caches a user's name when send any message.
        """

        async with self.bot.redis() as re:
            await re.set(f"UserName-{message.author.id}", str(message.author))

    @utils.Cog.listener()
    async def on_user_update(self, before:discord.User, after:discord.User):
        """
        Caches a username change into the redis cache.
        """

        if before.name == after.name:
            return
        async with self.bot.redis() as re:
            await re.set(f'UserName-{after.id}', str(after))


def setup(bot:utils.Bot):
    x = NameHandler(bot)
    bot.add_cog(x)
