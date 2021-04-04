from discord.ext import commands
import voxelbotutils as utils

from cogs.utils.checks.guild_is_server_specific import guild_is_server_specific


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

    async def predicate(ctx:utils.Context):
        # Bot support can do anything
        try:
            await utils.checks.is_bot_support().predicate(ctx)
            return True
        except Exception:
            pass

        # Make sure we're on Gold
        try:
            await guild_is_server_specific().predicate(ctx)
        except Exception:
            raise commands.NotServerSpecificBotModerator()

        # Make sure they have the role
        if any([i for i in ctx.author.roles if i.name.casefold() in 'marriagebot moderator']):
            return True
        raise commands.NotServerSpecificBotModerator()

    return commands.check(predicate)
