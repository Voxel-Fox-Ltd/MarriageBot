import re as regex

from discord.ext.commands import Cog as OriginalCog

from cogs.utils.custom_bot import CustomBot


class CustomCog(OriginalCog):
    """A simple lil wrapper around the original discord Cog class that just adds a
    logger for me to use"""

    def __init__(self, bot:CustomBot, logger_name:str=None):
        self.bot = bot
        if logger_name:
            self.logger = bot.logger.getChild(logger_name)
        else:
            self.logger = bot.logger.getChild(self.get_logger_name())

    def get_logger_name(self, *prefixes, sep:str='.') -> str:
        """Gets the name of the class with any given prefixes, with sep as a seperator"""
        return sep.join(['cog'] + list(prefixes) + [self.__cog_name__.replace(' ', '')])

    def get_name(self) -> str:
        """Gets the name of the class as a nice ol' space-seperated thingmie"""
        return regex.sub(r"(?:[A-Z])(?:(?:[a-z0-9])+|[A-Z]+$|[A-Z]+(?=[A-Z]))?", "\\g<0> ", self.__cog_name__.replace(' ', '')).strip()
