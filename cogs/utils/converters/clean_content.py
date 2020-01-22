import re as regex

from discord.ext import commands


class CleanContent(str):

    @classmethod
    async def convert(cls, ctx:commands.Context, argument:str):
        """Cleans up everyone and here mentions and leaves all else as is"""

        return regex.sub(r'@(everyone|here)', '@\u200b\\1', argument)
