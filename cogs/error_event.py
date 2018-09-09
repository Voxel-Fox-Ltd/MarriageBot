from gc import collect
from traceback import format_exc
from discord.ext.commands import Context
from discord.ext.commands import MissingRequiredArgument, BadArgument, CommandNotFound, CheckFailure, CommandInvokeError, CommandOnCooldown
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


    async def on_command_error(self, ctx:Context, error):
        '''
        Runs when there's an error thrown somewhere in the bot
        '''

        if ctx.author.id in self.bot.config['owners']:
            raise error

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
            if 'FORBIDDEN' in str(error):
                await ctx.author.send("I'm unable to send messages into that channel.")
                return
            elif 'oserror' in str(error).lower():
                number = collect()
                await self.log_channel.send(f'Deleted `{number}` unreachable objects from memory, <@141231597155385344>')
                await ctx.send('I was unable to run that command properly - try again in a moment.')
                return
            await ctx.author.send(f"Error encountered running that command: `{error!s}`")
            return
        elif isinstance(error, CommandOnCooldown):
            # Ratelimited user so no error text
            return
        elif isinstance(error, CheckFailure):
            # The only checks are the CalebOnly and hidden commands
            return
        elif isinstance(error, CommandNotFound):
            x = '\\n'.join(ctx.message.content.split('\n'))
            # print(f"Command not found: {x}")
        else:
            try: 
                raise error 
            except Exception as e:
                data = f"**Error**\nUser: `{ctx.author!s}` (`{ctx.author.id}`) | Guild: `{ctx.guild.name}` (`{ctx.guild.id}`) | Content: `{ctx.message.content}`\n" + "```py\n" + format_exc() + "```"
                try:
                    await self.log_channel.send(data)
                except Exception as e:
                    print(data)


def setup(bot:CustomBot):
    x = ErrorEvent(bot)
    bot.add_cog(x)
