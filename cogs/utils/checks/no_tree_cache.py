from discord.ext.commands import CheckFailure, Context, check


class IsTreeCached(CheckFailure):
    '''Catch-all for not donating errors'''
    pass


def no_tree_cache():
    '''The check to make sure that a given author is a Patreon sub'''

    async def predicate(ctx:Context):
        if ctx.author.id not in ctx.bot.tree_cache:
            return True 
        raise IsTreeCached()
    return check(predicate)
