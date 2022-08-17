from __future__ import annotations

from typing import Union

import discord
from discord.ext import commands, vbu

from cogs import utils


class NameHandler(vbu.Cog):

    async def save_name(self, user: Union[discord.User, discord.Member]):
        utils.DiscordNameManager.get(user.id).name = str(user)
        async with vbu.Redis() as re:
            await re.set(f"UserName-{user.id}", str(user))

    @vbu.Cog.listener()
    async def on_message(self, message: discord.Message):
        return await self.save_name(message.author)

    @vbu.Cog.listener()
    async def on_command(self, ctx: commands.Context):
        return await self.save_name(ctx.author)


def setup(bot: vbu.Bot):
    x = NameHandler(bot)
    bot.add_cog(x)
