from discord.ext import commands


class NotServerSpecific(commands.CheckFailure):
    """
    The error thrown when the bot is not set to server specific.
    """

    def __init__(self):
        super().__init__("This command can only be run with MarriageBot Gold.")


def guild_is_server_specific():
    """
    A check to make sure that the bot is set to server specific.
    """

    def predicate(ctx):
        if ctx.bot.config['is_server_specific']:
            return True
        raise NotServerSpecific()
    return commands.check(predicate)
