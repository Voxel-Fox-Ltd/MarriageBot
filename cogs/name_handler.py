import discord
from discord.ext import vbu


class NameHandler(vbu.Cog[vbu.Bot]):

    @vbu.Cog.listener()
    async def on_message(self, message: discord.Message):
        """
        Caches a user's name when send any message.
        """

        async with vbu.Redis() as re:
            await re.set(f"UserName-{message.author.id}", str(message.author))

    @vbu.Cog.listener()
    async def on_user_update(self, before: discord.User, after: discord.User):
        """
        Caches a username change into the redis cache.
        """

        if before.name == after.name:
            return
        if str(after).endswith("#0000"):
            return
        async with vbu.Redis() as re:
            await re.set(f'UserName-{after.id}', str(after))


def setup(bot: vbu.Bot):
    x = NameHandler(bot)
    bot.add_cog(x)
