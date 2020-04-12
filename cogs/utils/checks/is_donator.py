import discord
from discord.ext import commands


class IsNotDonator(commands.CheckFailure):
    """The base "not donator" error to join PayPal and Patreon"""

    pass


class IsNotPatreon(IsNotDonator):
    """Thrown when the given user is not a valid Patreon sub"""

    pass


class IsNotPaypal(IsNotDonator):
    """Thrown when the author is not a valid PayPal donator"""

    pass


async def is_patreon_predicate(bot:commands.Bot, user:discord.User, tier:int=1):
    """Returns True if the user is a Patreon sub

    Params:
        bot: commands.Bot
            The bot object
        user: discord.User
            The user (or generic snowflake object) that we want to check has the Patreon role
        tier: int = 1
            The tier of Patron we're lookin for
    """

    # Set the support guild if we have to
    if not bot.support_guild:
        try:
            await bot.fetch_support_guild()
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return False

    # Get member and look for role
    try:
        member = await bot.support_guild.fetch_member(user.id)
        if bot.config['patreon_roles'][tier - 1] in member._roles:
            return True
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        pass
    return False


async def get_patreon_tier(bot:commands.Bot, user:discord.User):
    """Returns True if the user is a Patreon sub

    Params:
        bot: commands.Bot
            The bot object
        user: discord.User
            The user (or generic snowflake object) that we want to check has the Patreon role
    """

    # Set the support guild if we have to
    if not bot.support_guild:
        try:
            await bot.fetch_support_guild()
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return 0

    # Get member and look for role
    try:
        member = await bot.support_guild.fetch_member(user.id)
        counter = 0
        for role_id in bot.config['patreon_roles']:
            if role_id in member._roles:
                counter += 1
        return counter
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        pass
    return 0


def is_patreon(tier:int=1):
    """The check to make sure that a given author is a Patreon sub"""

    async def predicate(ctx:commands.Context):
        user_tier = await get_patreon_tier(ctx.bot, ctx.author)
        if user_tier >= tier:
            return True
        raise IsNotPatreon()
    return commands.check(predicate)
