from __future__ import annotations

import discord
from discord.ext import commands, vbu

from cogs import utils


class BlockCommands(vbu.Cog[utils.types.Bot]):

    @commands.command(
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="user",
                    description="The user that you want to block.",
                    type=discord.ApplicationCommandOptionType.user,
                ),
            ],
        ),
    )
    @commands.defer()
    @commands.bot_has_permissions(send_messages=True)
    async def block(
            self,
            ctx: vbu.Context,
            user: vbu.converters.UserID):
        """
        Blocks a user from being able to adopt/makeparent/etc you.
        """

        # Make sure it's not the author
        if ctx.author.id == user:
            return await ctx.send("You can't block yourself .-.")

        # Add to db and cache
        async with vbu.Database() as db:
            await db(
                """
                INSERT INTO
                    blocked_user
                    (
                        user_id,
                        blocked_user_id
                    )
                VALUES
                    (
                        $1,
                        $2
                    )
                ON CONFLICT (user_id, blocked_user_id)
                DO NOTHING
                """,
                ctx.author.id, user,
            )
        async with vbu.Redis() as re:
            await re.publish("BlockedUserAdd", {"user_id": ctx.author.id, "blocked_user_id": user})

        # And respond
        return await ctx.send("That user is now blocked.")

    @commands.command(
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="user",
                    description="The user that you want to unblock.",
                    type=discord.ApplicationCommandOptionType.user,
                ),
            ],
        ),
    )
    @commands.defer()
    @commands.bot_has_permissions(send_messages=True)
    async def unblock(
            self,
            ctx: vbu.Context,
            user: vbu.converters.UserID):
        """
        Unblocks a user and allows them to adopt/makeparent/etc you.
        """

        # Make sure it's not the author
        if ctx.author.id == user:
            return await ctx.send("You can't block yourself .-.")

        # Add to db and cache
        async with vbu.Database() as db:
            await db(
                """
                DELETE FROM
                    blocked_user
                WHERE
                    user_id = $1
                AND
                    blocked_user_id = $2
                """,
                ctx.author.id, user,
            )
        async with vbu.Redis() as re:
            await re.publish("BlockedUserRemove", {"user_id": ctx.author.id, "blocked_user_id": user})

        # And respond
        return await ctx.send("That user is now unblocked.")


def setup(bot: utils.types.Bot):
    x = BlockCommands(bot)
    bot.add_cog(x)
