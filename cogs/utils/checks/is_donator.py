from discord.ext.commands import CheckFailure, Context, check


class IsNotDonator(CheckFailure):
    '''Catch-all for not donating errors'''
    pass


class IsNotPatreon(IsNotDonator): pass
class IsNotPaypal(IsNotDonator): pass


async def is_patreon_predicate(bot, user, tier=1):
    '''Returns True if the user is a Patreon sub'''

    # # Make sure both settings are set
    # if bot.config.get('guild') in [None, ''] or bot.config.get('patreon_roles') in [None, '']:
    #     return None

    # Set the support guild
    if not bot.support_guild:
        guild_id = ctx.bot.config['guild_id']
        guild = await bot.fetch_guild(guild_id)
        bot.support_guild = guild

    # Get member and look for role
    try:
        member = await bot.support_guild.fetch_member(user.id)
        if bot.config['patreon_roles'][tier-1] in [i.id for i in member.roles]:
            return True
    except Exception:
        pass
    return False


def is_patreon(tier:int=1):
    '''The check to make sure that a given author is a Patreon sub'''

    async def predicate(ctx:Context):
        if await is_patreon_predicate(ctx.bot, ctx.author, tier):
            return True 
        raise IsNotPatreon()
    return check(predicate)
