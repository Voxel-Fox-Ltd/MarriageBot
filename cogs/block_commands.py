import discord
from discord.ext import commands
import voxelbotutils as utils


class BlockCommands(utils.Cog):

    @utils.command()
    @commands.bot_has_permissions(send_messages=True)
    async def block(self, ctx:utils.Context, user:utils.converters.UserID):
        """
        Blocks a user from being able to adopt/makeparent/etc you.
        """

        # Make sure it's not the author
        if ctx.author.id == user:
            return await ctx.send("You can't block yourself .-.")

        # Add to list
        async with self.bot.database() as db:
            await db(
                """INSERT INTO blocked_user (user_id, blocked_user_id) VALUES ($1, $2)
                ON CONFLICT (user_id, blocked_user_id) DO NOTHING""",
                ctx.author.id, user,
            )
        async with self.bot.redis() as re:
            await re.publish("BlockedUserAdd", {"user_id": ctx.author.id, "blocked_user_id": user})
        return await ctx.send("That user is now blocked.")

    @utils.command()
    @commands.bot_has_permissions(send_messages=True)
    async def unblock(self, ctx:utils.Context, user:utils.converters.UserID):
        """
        Unblocks a user and allows them to adopt/makeparent/etc you.
        """

        # Make sure it's not the author
        if ctx.author.id == user:
            return await ctx.send("You can't block yourself .-.")

        # Remove from list
        async with self.bot.database() as db:
            await db(
                """DELETE FROM blocked_user WHERE user_id=$1 AND blocked_user_id=$2""",
                ctx.author.id, user,
            )
        async with self.bot.redis() as re:
            await re.publish("BlockedUserRemove", {"user_id": ctx.author.id, "blocked_user_id": user})
        return await ctx.send("That user is now unblocked.")


def setup(bot:utils.Bot):
    x = BlockCommands(bot)
    bot.add_cog(x)
