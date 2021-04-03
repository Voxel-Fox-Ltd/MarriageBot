import discord
from discord.ext import commands
import voxelbotutils as utils


class BlockCommands(utils.Cog):

    @utils.command()
    @commands.bot_has_permissions(send_messages=True)
    async def block(self, ctx:utils.Context, user_id:utils.converters.UserID):
        """
        Blocks a user from being able to adopt/makeparent/whatever you.
        """

        # Get current blocks
        current_blocks = self.bot.blocked_users.get(ctx.author.id, list())
        if user_id in current_blocks:
            return await ctx.send("That user is already blocked.")

        # Add to list
        async with self.bot.database() as db:
            await db(
                'INSERT INTO blocked_user (user_id, blocked_user_id) VALUES ($1, $2)',
                ctx.author.id, user_id
            )
        async with self.bot.redis() as re:
            await re.publish("BlockedUserAdd", {"user_id": ctx.author.id, "blocked_user_id": user_id})
        return await ctx.send("That user is now blocked.")

    @utils.command()
    @commands.bot_has_permissions(send_messages=True)
    async def unblock(self, ctx:utils.Context, user:utils.converters.UserID):
        """
        Unblocks a user and allows them to adopt/makeparent/whatever you.
        """

        # Get current blocks
        current_blocks = self.bot.blocked_users[ctx.author.id]
        if user not in current_blocks:
            return await ctx.send("You don't have that user blocked.")

        # Remove from list
        async with self.bot.database() as db:
            await db(
                'DELETE FROM blocked_user WHERE user_id=$1 AND blocked_user_id=$2',
                ctx.author.id, user
            )
        async with self.bot.redis() as re:
            await re.publish("BlockedUserRemove", {"user_id": ctx.author.id, "blocked_user_id": user})
        return await ctx.send("That user is now unblocked.")


def setup(bot:utils.Bot):
    x = BlockCommands(bot)
    bot.add_cog(x)
