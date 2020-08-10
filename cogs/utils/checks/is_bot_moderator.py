import discord
from discord.ext import commands

from cogs.utils.checks.is_server_specific import NotServerSpecific


class NotBotModerator(commands.CommandError):
    """Thrown when the user isn't set as a bot moderator"""

    pass


class NotBotSupport(NotBotModerator):
    """Thrown when the user isn't set as a bot administrator"""

    pass


async def is_bot_support_predicate(ctx:commands.Context):
    """Returns True if the user is on the support guild with the bot moderator role"""

    # Make sure both settings are set
    if ctx.bot.config.get('bot_admin_role') in [None, '']:
        ctx.bot.logger.warn("No bot admin role set in the config")
        return False

    # Set the support guild if we have to
    if not ctx.bot.support_guild:
        await ctx.bot.fetch_support_guild()

    # Get member and look for role
    try:
        member = await ctx.bot.support_guild.fetch_member(ctx.author.id)
        if ctx.bot.config['bot_admin_role'] in member._roles:
            return True
    except (discord.NotFound, discord.HTTPException):
        pass
    return False


def is_bot_support():
    """Checks whether the bot is set as an administrator"""

    async def predicate(ctx:commands.Context):
        if await is_bot_support_predicate(ctx):
            return True
        raise NotBotSupport()
    return commands.check(predicate)


def is_server_specific_bot_moderator():
    """Check to see if the user has a role either called 'MarriageBot Moderator' or 'SSF MarriageBot Moderator'"""

    async def predicate(ctx:commands.Context):
        if await is_bot_support_predicate(ctx):
            return True  # If they're MB support
        if not ctx.bot.config['server_specific']:
            raise NotServerSpecific()  # If it's not server specific
        if any([i for i in ctx.author.roles if i.name.casefold() in ('ssf marriagebot moderator', 'marriagebot moderator')]):
            return True  # Ye it's all good
        raise NotBotModerator()
    return commands.check(predicate)
