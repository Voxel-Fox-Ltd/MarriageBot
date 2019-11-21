from discord.ext.commands import CheckFailure, check
from discord.ext import commands


class NotServerSpecific(commands.CheckFailure):
    """The error thrown when the bot is not set to server specific"""
    pass


def is_server_specific():
    """A check to make sure that the bot is set to server specific"""

    def predicate(ctx):
        if ctx.bot.is_server_specific:
            return True
        raise NotServerSpecific()
    return commands.check(predicate)
