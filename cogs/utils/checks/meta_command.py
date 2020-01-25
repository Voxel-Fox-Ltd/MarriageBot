from discord.ext import commands


class InvokedMetaCommand(commands.CheckFailure):
    """Raised on any command decorated with @meta_command
    This stops users from running commands that we've made for internal use only"""


def meta_command():
    """Stops users from being able to run this command
    Should be caught and then reinvoked"""

    def predicate(ctx):
        raise InvokedMetaCommand()
    return commands.check(predicate)
