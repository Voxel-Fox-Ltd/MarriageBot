import re as regex

from discord.ext import commands


class UserID(int):
    """A conveter that takes the given value and tries to grab the ID from it
    Returns the ID of the user"""

    USER_ID_REGEX = regex.compile(r'([0-9]{15,21})')

    @classmethod
    async def convert(cls, ctx:commands.Context, value:str) -> int:
        """Converts the given value to a valid user ID"""

        # Maybe they gave a straight?
        try:
            return int(value)
        except ValueError:
            pass

        # They pinged the user
        match = cls.USER_ID_REGEX.search(value)
        if match is not None:
            return int(match.group(1))
        raise commands.BadArgument()
