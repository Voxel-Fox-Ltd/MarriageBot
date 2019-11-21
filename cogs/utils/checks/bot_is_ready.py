# from discord.ext.commands import CheckFailure, Context, check
from discord.ext import commands


class BotNotReady(commands.CheckFailure):
    """The generic error for the bot failing the bot_is_ready check"""

    pass


def bot_is_ready():
    """The check for whether the bot has cached all of its data yet"""

    async def predicate(ctx:commands.Context):
        if ctx.bot.is_ready():
            return True
        raise BotNotReady
    return commands.check(predicate)
