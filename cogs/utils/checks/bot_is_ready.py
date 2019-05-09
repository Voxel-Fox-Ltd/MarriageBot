from discord.ext.commands import CheckFailure, Context, check


class BotNotReady(CheckFailure):
    pass


def bot_is_ready():
    async def predicate(ctx:Context):
        if ctx.bot.is_ready():
            return True 
        raise BotNotReady 
    return check(predicate)
