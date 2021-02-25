from discord.ext import commands


class BlockedUserError(commands.CommandError):
    """The error raised when a given user is blocked by the author"""


class UnblockedMember(commands.MemberConverter):
    """
    A modified member converter to automatically checked if the author
    is blocked by the given user.
    """

    async def convert(self, ctx:commands.Context, argument:str):
        user = await super().convert(ctx, argument)
        async with ctx.bot.database() as db:
            data = await db("SELECT * FROM blocked_user WHERE user_id=$1 AND blocked_user_id=$2", user.id, ctx.author.id)
        if data:
            raise BlockedUserError(f"You have been blocked by {user.mention}.")
        return user
