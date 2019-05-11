from logging import getLogger

from discord.ext.commands import Cog as OriginalCog


class Cog(OriginalCog):

    def __init__(self, cog_name:str):
        self.log_handler = getLogger(f"marriagebot.cogs.{cog_name}")
