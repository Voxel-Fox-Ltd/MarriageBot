import re as regex

from discord.ext import commands

from cogs.utils.family_tree.family_tree_member import FamilyTreeMember


class UserID(commands.IDConverter):
    """A conveter that takes the given value and tries to grab the ID from it
    Returns the ID of the user"""

    USER_ID_REGEX = regex.compile(r'([0-9]{15,21})')

    @classmethod
    async def convert(cls, ctx:commands.Context, value:str) -> int:
        """Converts the given value to a valid user ID"""

        match = cls.USER_ID_REGEX.search(value)
        if match is not None:
            return int(match.group(1))
        raise commands.BadArgument(f"I couldn't convert `{value}` into a user! Try pinging them, or giving their ID.")
