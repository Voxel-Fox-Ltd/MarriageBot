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
            raise

        # Make sure this is in a guild
        await commands.guild_only().predicate(ctx)

        # Make sure they have the role
        mb_mod_roles = [i for i in ctx.guild.roles if i.name.casefold() == 'marriagebot moderator']
        if not mb_mod_roles:
            raise commands.CheckFailure("Create a role with the name `MarriageBot Moderator` and give it to yourself to be able to run this command.")
        if any([i for i in ctx.author.roles if i in mb_mod_roles]):
            return True
        raise NotServerSpecificBotModerator()

    return commands.check(predicate)
