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


    @property
    def event_log_channel(self):
        channel_id = self.bot.config['event_log_channel']
        channel = self.bot.get_channel(channel_id)
        return channel


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

        # OSError
        elif isinstance(error, CommandInvokeError):
            # Something dumb with the ram
            if 'oserror' in str(error).lower():
                number = collect()
                data = f"**Error**\nUser: `{ctx.author!s}` (`{ctx.author.id}`) | Guild: `{ctx.guild.name}` (`{ctx.guild.id}`) | Content: `{ctx.message.content}`\n" + "```py\n" + format_exc() + "```"
                try:
                    await self.event_log_channel.send(data)
                except Exception:
                    print(data)
                await self.event_log_channel.send(f'Deleted `{number}` unreachable objects from memory, <@141231597155385344>')
                await ctx.send('I was unable to run that command properly - try again in a moment.')
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
