from discord.ext import commands


class BlockedUserError(commands.CommandError):
    """The error raised when a given user is blocked by the author"""

    pass


class UnblockedMember(commands.MemberConverter):
    """A modified member converter to automatically checked if the author
    is blocked by the given user"""

    async def convert(self, ctx: commands.Context, argument: str):
        user = await super().convert(ctx, argument)
        if ctx.author.id in ctx.bot.blocked_users.get(user.id, list()):
            raise BlockedUserError(f"You have been blocked by `{user!s}`.")
        return user
