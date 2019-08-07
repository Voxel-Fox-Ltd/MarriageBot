from discord.ext.commands import CheckFailure, check


class NotServerSpecific(CheckFailure):
    pass


def is_server_specific():
    def predicate(ctx):
        if ctx.bot.is_server_specific:
            return True
        raise NotServerSpecific()
    return check(predicate)
