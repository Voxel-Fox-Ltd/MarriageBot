from __future__ import annotations

import discord
from discord.ext import vbu


class NameHandler(vbu.Cog):

    @vbu.Cog.listener()
    async def on_message(self, message: discord.Message):
        """
        Caches a user's name when send any message.
        """

        async with vbu.Redis() as re:
            await re.set(f"UserName-{message.author.id}", str(message.author))


def setup(bot: vbu.Bot):
    x = NameHandler(bot)
    bot.add_cog(x)
