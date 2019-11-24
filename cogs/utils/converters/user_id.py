import discord
from discord.ext import commands


class UserID(commands.UserConverter):
    """A conveter that takes the given value and tries to grab the ID from it
    Returns the ID of the user"""

    async def convert(self, ctx:commands.Context, value:str) -> int:
        """Converts the given value to a valid user ID"""

        # It could be a user
        try:
            return (await super().convert(ctx, value)).id
        except commands.BadArgument as e:
            pass

        # It could be an int
        try:
            return int(value)
        except ValueError:
            pass

        # Something inbetween?
        match = self._get_id_match(value)
        if match is None:
            raise e
        return int(match.group(1))
