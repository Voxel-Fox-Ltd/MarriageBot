import discord
from discord.ext.commands import MissingPermissions, Context, check, MissingRole

from cogs.utils.checks.is_server_specific import NotServerSpecific


async def is_bot_moderator_predicate(ctx:Context):
    '''Returns True if the user is a bot moderator'''

    logger = ctx.bot.logger.getChild('checks.is_bot_moderator')

    # Make sure both settings are set
    if ctx.bot.config.get('guild_id') in [None, '']:
        logger.warn("No guild ID set in the bot config")
        return None
    elif ctx.bot.config.get('bot_admin_role') in [None, '']:
        logger.warn("No bot admin role set in the config")
        return None

    # Set the support guild
    if not ctx.bot.support_guild:
        guild_id = ctx.bot.config['guild_id']
        try:
            guild = await ctx.bot.fetch_guild(guild_id)
        except Exception:
            logger.warn("Could not fetch the guild ID")
            return None
        ctx.bot.support_guild = guild

    # Get member and look for role
    try:
        member = await ctx.bot.support_guild.fetch_member(ctx.author.id)
        if ctx.bot.config['bot_admin_role'] in [i.id for i in member.roles]:
            return True
    except (AttributeError, discord.NotFound, discord.Forbidden):
        pass
    return False


def is_bot_moderator(permission:str='MarriageBot moderator'):
    '''The check to make sure that a given author is a bot mod'''

    async def predicate(ctx:Context):
        if await is_bot_moderator_predicate(ctx):
            return True
        raise MissingPermissions([permission])
    return check(predicate)


def is_server_specific_bot_moderator():
    """Check to see if the user has a role either called 'MarriageBot Moderator' or 'SSF MarriageBot Moderator'"""

    async def predicate(ctx:Context):
        if await is_bot_moderator_predicate(ctx):
            return True
        if not ctx.bot.config['server_specific']:
            raise NotServerSpecific
        if any([i for i in ctx.author.roles if i.name.casefold() in ('ssf marriagebot moderator', 'marriagebot moderator')]):
            return True
        raise MissingRole('SSF MarriageBot Moderator')
    return check(predicate)
