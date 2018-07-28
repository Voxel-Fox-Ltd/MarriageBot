from traceback import format_exc
from discord.ext.commands import Context
from discord.ext.commands import MissingRequiredArgument, BadArgument, CommandNotFound, CheckFailure, CommandInvokeError
from cogs.utils.custom_bot import CustomBot
from cogs.utils.checks.can_send_files import CantSendFiles


class ErrorEvent(object):

    def __init__(self, bot:CustomBot):
        self.bot = bot


    @property
    def log_channel(self):
        channel_id = self.bot.config['log_channel']
        channel = self.bot.get_channel(channel_id)
        return channel   


    async def on_command(self, ctx:Context):
        '''
        Runs when a command is run
        '''

        await self.log_channel.send(f"Guild: `{ctx.guild.name}` (`{ctx.guild.id}`) | User: `{ctx.author!s}` (`{ctx.author.id}`)\nContent: `{ctx.message.content}`")


    async def on_command_error(self, ctx:Context, error):
        '''
        Runs when there's an error thrown somewhere in the bot
        '''

        if isinstance(error, MissingRequiredArgument):
            await ctx.send(f"You passed too few arguments to use that command.")
            return
        elif isinstance(error, BadArgument):
            await ctx.send(f"Unfortunately, that isn't a valid argument for this command.")
            return
        elif isinstance(error, CantSendFiles):
            await ctx.send("I'm not able to send files into this channel.")
            return
        elif isinstance(error, CommandInvokeError):
            await ctx.author.send("I'm unable to send messages in that channel.")
            return
        elif isinstance(error, CheckFailure):
            # The only checks are the CalebOnly commands
            return
        elif isinstance(error, CommandNotFound):
            x = '\\n'.join(ctx.message.content.split('\n'))
            print(f"Command not found: {x}")
        else:
            try: 
                raise error 
            except Exception as e:
                await self.log_channel.send(
                    f"**Error**\nUser: `{ctx.author!s}` (`{ctx.author.id}`) | Guild: `{ctx.guild.name}` (`{ctx.guild.id}`) | Content: `{ctx.message.content}`\n" + 
                    "```py\n" + format_exc() + "```"
                    )


def setup(bot:CustomBot):
    x = ErrorEvent(bot)
    bot.add_cog(x)
