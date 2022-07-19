import discord
from discord.ext import commands, vbu


__all__ = (
    'BlockedUserError',
    'UnblockedMember',
)


class BlockedUserError(commands.BadArgument):
    """
    The error raised when a given user is blocked by the author.
    """


class UnblockedMember(discord.Member):
    """
    A modified member converter to automatically checked if the
    author is blocked by the given user.
    """

    @classmethod
    async def convert(
            cls,
            ctx: vbu.Context,
            argument: str):
        user = await commands.MemberConverter().convert(ctx, argument)
        async with vbu.Database() as db:
            data = await db.call(
                """
                SELECT
                    *
                FROM
                    blocked_user
                WHERE
                    user_id = $1
                AND
                    blocked_user_id = $2
                """,
                user.id, ctx.author.id,
            )
        if data:
            raise BlockedUserError(f"You have been blocked by {user.mention}.")
        return user
