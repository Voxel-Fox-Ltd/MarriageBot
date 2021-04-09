from datetime import datetime as dt, timedelta

from discord.ext import commands


class IsNotVoter(commands.CheckFailure):
    """The error thrown when a particular user is not a voter"""

    pass


def is_voter_predicate(ctx: commands.Context):
    """Returns True if the user has voted within the last 12 hours
    Provided as a predicate so it can be used as a util"""

    timestamp = ctx.bot.dbl_votes.get(ctx.author.id)  # Get vote timestamp
    if not timestamp:
        return False  # They have none
    if timestamp > dt.now() - timedelta(hours=12):
        return True  # It was within 12 hours
    return False  # It wasn't within 12 hours


def is_voter():
    """A check to make sure the author of a given command is a voter"""

    async def predicate(ctx: commands.Context):
        if is_voter_predicate(ctx):
            return True
        raise IsNotVoter()

    return commands.check(predicate)
