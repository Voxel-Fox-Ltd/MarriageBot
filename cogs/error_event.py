from gc import collect
from traceback import format_exc

from discord.ext.commands import Context, Cog
from discord.ext.commands import MissingRequiredArgument, BadArgument, CommandNotFound, CheckFailure, CommandInvokeError, CommandOnCooldown, NotOwner, MissingPermissions

from cogs.utils.custom_bot import CustomBot
from cogs.utils.checks.can_send_files import CantSendFiles


class ErrorEvent(Cog):

    def __init__(self, bot:CustomBot):
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

        # Throw errors properly for me
        if ctx.author.id in self.bot.config['owners']:
            text = f'```py\n{error}```'
            await ctx.send(text)
            raise error

        # Missing argument error
        if isinstance(error, MissingRequiredArgument):
            await ctx.send(f"You passed too few arguments to use that command.")
            return

        # Bad converter error
        elif isinstance(error, BadArgument):
            await ctx.send(f"Unfortunately, that isn't a valid argument for this command.")
            return

        # Forbidden error
        elif isinstance(error, CantSendFiles):
            try:
                await ctx.send("I'm not able to send files into this channel.")
            except Exception:
                await ctx.author.send("I'm unable to send messages into that channel.")
            return

        # Can't run the command 
        elif isinstance(error, (MissingPermissions, NotOwner)):
            await ctx.send("You're missing the required permissions to run that command.")
            return

        # Command doesn't run
        elif isinstance(error, CommandInvokeError):
            # Can't message channel
            if 'FORBIDDEN' in str(error):
                await ctx.author.send("I'm unable to send messages into that channel.")
                return

            # Something dumb with the ram
            elif 'oserror' in str(error).lower():
                number = collect()
                data = f"**Error**\nUser: `{ctx.author!s}` (`{ctx.author.id}`) | Guild: `{ctx.guild.name}` (`{ctx.guild.id}`) | Content: `{ctx.message.content}`\n" + "```py\n" + format_exc() + "```"
                try:
                    await self.event_log_channel.send(data)
                except Exception:
                    print(data)
                await self.event_log_channel.send(f'Deleted `{number}` unreachable objects from memory, <@141231597155385344>')
                await ctx.send('I was unable to run that command properly - try again in a moment.')
                return

        # Command ratelimited
        elif isinstance(error, CommandOnCooldown):
            # Let owners actually run it
            if ctx.author.id in self.bot.config['owners']:
                await ctx.reinvoke()
            return

        # Check failed for no particular reason
        elif isinstance(error, CheckFailure):
            return

        # Command not found
        elif isinstance(error, CommandNotFound):
            return

        # An error I didn't account for? Weird.
        else:
            try: 
                raise error 
            except Exception:
                data = f"**Error**\nUser: `{ctx.author!s}` (`{ctx.author.id}`) | Guild: `{ctx.guild.name}` (`{ctx.guild.id}`) | Content: `{ctx.message.content}`\n" + "```py\n" + format_exc() + "```"
                print(data)


def setup(bot:CustomBot):
    x = ErrorEvent(bot)
    bot.add_cog(x)
