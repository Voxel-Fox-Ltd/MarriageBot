from discord.ext.commands import CheckFailure, Context, check


class IsNotDonator(CheckFailure):
    '''Catch-all for not donating errors'''
    pass


class IsNotPatreon(IsNotDonator): pass
class IsNotPaypal(IsNotDonator): pass


async def is_patreon_predicate(bot, user):
    '''Returns True if the user is a Patreon sub'''

    if not bot.support_guild:
        support_invite = await bot.fetch_invite(bot.config['guild'])
        guild_id = support_invite.guild.id
        guild = await bot.fetch_guild(guild_id)
        bot.support_guild = guild
    try:
        member = await bot.support_guild.fetch_member(user.id)
        if bot.config['patreon_sub_role'] in [i.id for i in member.roles]:
            return True
    except Exception:
        pass
    return False


def is_patreon():
    '''The check to make sure that a given author is a Patreon sub'''

    async def predicate(ctx:Context):
        if await is_patreon_predicate(ctx.bot, ctx.author):
            return True 
        raise IsNotPatreon()
    return check(predicate)
