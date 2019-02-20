from discord.ext.commands import command, Context, cooldown as original_cooldown, check


def cooldown(*args):
    async def predicate(ctx:Context):
        if ctx.author.id in ctx.bot.config['owners']:
            return True 
        return original_cooldown(*args)
    return check(predicate)
