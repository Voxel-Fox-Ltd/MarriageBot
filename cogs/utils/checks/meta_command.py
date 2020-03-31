from discord.ext import commands


class InvokedMetaCommand(commands.CheckFailure):
    """Raised on any command decorated with @meta_command
    This stops users from running commands that we've made for internal use only"""


def meta_command():
    """Stops users from being able to run this command
    Should be caught and then reinvoked OR have ctx.invoke_meta set to True"""

    def predicate(ctx):
        if getattr(ctx, 'invoke_meta', False):
            return True
        raise InvokedMetaCommand()
    return commands.check(predicate)
