from discord.ext.commands import Context
from discord.ext.commands import MissingRequiredArgument, BadArgument, CommandNotFound
from cogs.utils.custom_bot import CustomBot
from cogs.utils.checks.can_send_files import CantSendFiles


class ErrorEvent(object):

    def __init__(self, bot:CustomBot):
        self.bot = bot


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
        elif isinstance(error, CommandNotFound):
            x = '\\n'.join(ctx.message.content.split('\n'))
            print(f"Command not found: {x}")
        else:
            raise error


def setup(bot:CustomBot):
    x = ErrorEvent(bot)
    bot.add_cog(x)
