from gc import collect
from traceback import format_exc

from discord.errors import Forbidden
from discord.ext.commands import Context
from discord.ext.commands import MissingRequiredArgument, BadArgument, CommandNotFound, CheckFailure, CommandInvokeError, CommandOnCooldown, NotOwner, MissingPermissions

from cogs.utils.custom_bot import CustomBot
from cogs.utils.checks.can_send_files import CantSendFiles
from cogs.utils.custom_cog import Cog


class ErrorEvent(Cog):

    def __init__(self, bot:CustomBot):
        super().__init__(self.__class__.__name__)
        self.bot = bot


    @Cog.listener()
    async def on_command_error(self, ctx:Context, error):
        '''
        Runs when there's an error thrown somewhere in the bot
        '''

        # Forbidden error
        if isinstance(error, CantSendFiles):
            try:
                await ctx.send("I'm not able to send files into this channel.")
            except Exception:
                await ctx.author.send("I'm unable to send messages into that channel.")
            return

        # Can't send message to channel
        elif isinstance(error, Forbidden):
            try:
                await ctx.author.send("I'm unable to send messages into that channel.")
            except Forbidden:
                pass
            return
                
        # Check failed for no particular reason
        elif isinstance(error, CheckFailure):
            return

        # Command not found
        elif isinstance(error, CommandNotFound):
            return


def setup(bot:CustomBot):
    x = ErrorEvent(bot)
    bot.add_cog(x)
