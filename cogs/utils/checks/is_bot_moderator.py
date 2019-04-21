from discord.ext.commands import MissingPermissions, Context, check


async def is_bot_moderator_predicate(ctx:Context):
    '''Returns True if the user is a bot moderator'''

    support_invite = await ctx.bot.fetch_invite(ctx.bot.config['guild'])
    support_guild = support_invite.guild 
    bot_admin_role = support_guild.get_role(ctx.bot.config['bot_admin_role'])
    try:
        if bot_admin_role in support_guild.get_member(ctx.author.id).roles:
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
