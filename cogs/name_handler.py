from __future__ import annotations

from typing import Optional, Union

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

    @commands.command(
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="user",
                    description="The user whose username you want to update.",
                    type=discord.ApplicationCommandOptionType.user,
                    required=False,
                ),
            ],
        ),
    )
    async def updatename(self, ctx: commands.Context, user: Optional[discord.User] = None):
        """
        Update a saved name inside of MarriageBot.
        """

        await self.save_name(user or ctx.author)
        await ctx.send("Updated :)")


def setup(bot: vbu.Bot):
    x = NameHandler(bot)
    bot.add_cog(x)
