import discord
from discord.ext import commands


class UserID(commands.Converter):
    """A conveter that takes the given value and tries to grab the ID from it

    First it runs UserConverter, then it tries to int value, then it checks
    if the value is a mention, before finally giving up

    Returns the ID of the user"""

    async def convert(self, ctx:commands.Context, value:str) -> int:
        """Converts the given value to a valid user ID"""

        # Try userconverter
        try:
            v: discord.User = await commands.UserConverter().convert(ctx, value)
            if v:
                return v.id
        except commands.BadArgument:
            pass

        # Try int (see if it's an ID already)
        try:
            return int(value)
        except ValueError:
            pass

        # See if it's a mention
        try:
            return int(value.strip('<>!@'))
        except ValueError:
            pass

        # Ah well
        raise commands.BadArgument()
