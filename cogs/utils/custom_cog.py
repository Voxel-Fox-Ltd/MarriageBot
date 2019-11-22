from discord.ext.commands import Cog as OriginalCog

from cogs.utils.custom_bot import CustomBot


class Cog(OriginalCog):
    """A simple lil wrapper around the original discord Cog class that just adds a
    logger for me to use"""

    def __init__(self, bot:CustomBot, logger_name:str=None):
        self.bot = bot
        if logger_name:
            self.log_handler = bot.logger.getChild(logger_name)
        else:
            self.log_handler = bot.logger.getChild(self.get_class_name('cog'))

    def get_class_name(self, *prefixes, sep:str='.'):
        """Gets the name of the class with any given prefixes, with sep as a seperator"""
        return sep.join(list(prefixes) + [self.__class__.__name__])
