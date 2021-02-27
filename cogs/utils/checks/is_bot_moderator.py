from discord.ext import commands
import voxelbotutils as utils

from cogs.utils.checks.is_server_specific import is_server_specific


class NotServerSpecificBotModerator(commands.MissingRole):
    """
    The specified user doesn't have the MarriageBot Moderator role.
    """

    def __init__(self):
        super().__init__("MarriageBot Moderator")


def is_server_specific_bot_moderator():
    """
    Check to see if the user has a role called 'MarriageBot Moderator'.
    """

    async def predicate(ctx:commands.Context):
        try:
            await utils.checks.is_bot_support().predicate(ctx)
            return True
        except Exception:
            pass
        await is_server_specific().predicate(ctx)
        if any([i for i in ctx.author.roles if i.name.casefold() in 'marriagebot moderator']):
            return True
        raise commands.NotServerSpecificBotModerator()
    return commands.check(predicate)
