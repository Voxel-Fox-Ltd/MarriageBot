import re as regex

from discord.ext import commands


class CleanContent(commands.Converter):

    async def convert(self, argument:str):
        """Cleans up everyone and here mentions and leaves all else as is"""

        return regex.sub(r'@(everyone|here)', '@\u200b\\1', argument)
