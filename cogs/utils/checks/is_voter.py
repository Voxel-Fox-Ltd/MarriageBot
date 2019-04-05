from datetime import datetime as dt, timedelta

from discord.ext.commands import CheckFailure, Context, check


class IsNotVoter(CheckFailure):
    '''The error thrown when a particular user is not a voter'''
    pass


def is_voter_predicate(ctx:Context):
    '''Returns True if the user has voted within the last 12 hours'''

    timestamp = ctx.bot.dbl_votes.get(ctx.author.id)
    if not timestamp:
        return False 
    if timestamp > dt.now() - timedelta(hours=12):
        return True 
    return False


def is_voter():
    '''The check to make sure that a given author is a voter'''

    async def predicate(ctx:Context):
        if is_voter_predicate(ctx):
            return True 
        raise IsNotVoter()
    return check(predicate)
