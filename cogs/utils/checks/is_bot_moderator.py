from discord.ext.commands import MissingPermissions, Context, check


async def is_bot_moderator_predicate(ctx:Context):
    '''Returns True if the user is a bot moderator'''

    # Make sure both settings are set
    if ctx.bot.config.get('guild') in [None, ''] or ctx.bot.config.get('bot_admin_role') in [None, '']:
        return None

    # Set the support guild
    if not ctx.bot.support_guild:
        support_invite = await ctx.bot.fetch_invite(ctx.bot.config['guild'])
        guild_id = support_invite.guild.id
        guild = await bot.fetch_guild(guild_id)
        ctx.bot.support_guild = guild

    # Get member and look for role
    try:
        member = await bot.support_guild.fetch_member(user.id)
        if bot.config['bot_admin_role'] in [i.id for i in member.roles]:
            return True
    except Exception:
        pass
    return False


def is_bot_moderator():
    '''The check to make sure that a given author is a bot mod'''

    async def predicate(ctx:Context):
        if await is_bot_moderator_predicate(ctx):
            return True 
        raise MissingPermissions(['MarriageBot moderator'])
    return check(predicate)
