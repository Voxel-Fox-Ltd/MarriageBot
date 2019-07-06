from discord.ext.commands import MissingPermissions, Context, check


async def is_bot_moderator_predicate(ctx:Context):
    '''Returns True if the user is a bot moderator'''

    # Make sure both settings are set
    if ctx.bot.config.get('guild_id') in [None, ''] or ctx.bot.config.get('bot_admin_role') in [None, '']:
        return None

    # Set the support guild
    if not ctx.bot.support_guild:
        guild_id = ctx.bot.config['guild_id']
        guild = await ctx.bot.fetch_guild(guild_id)
        ctx.bot.support_guild = guild

    # Get member and look for role
    try:
        member = await ctx.bot.support_guild.fetch_member(ctx.author.id)
        if ctx.bot.config['bot_admin_role'] in [i.id for i in member.roles]:
            return True
    except AttributeError:
        pass
    return False


def is_bot_moderator():
    '''The check to make sure that a given author is a bot mod'''

    async def predicate(ctx:Context):
        if await is_bot_moderator_predicate(ctx):
            return True 
        raise MissingPermissions(['MarriageBot moderator'])
    return check(predicate)
