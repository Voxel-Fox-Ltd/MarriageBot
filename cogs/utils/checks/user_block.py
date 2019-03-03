from discord import Member
from discord.ext.commands import check, Context, CommandError, MemberConverter

class BlockedUserError(CommandError):
    pass



class UnblockedMember(MemberConverter):

    async def convert(self, ctx:Context, argument:str):
        user = await super().convert(ctx, argument)
        if ctx.author.id in ctx.bot.blocked_users.get(user.id, list()):
            raise BlockedUserError()
        return user
