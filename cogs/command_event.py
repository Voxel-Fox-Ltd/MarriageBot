from discord import Message
from discord.ext.commands import Context
from cogs.utils.custom_bot import CustomBot


class CommandEvent(object):

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


    async def on_message(self, message:Message):
        if message.author.bot:
            return
        if any([i in message.content.casefold() for i in ['marriagebot', 'marriage bot', f'{self.bot.user.id}']]):
            await self.log_channel.send(f"Guild: `{message.guild.name}` (`{message.guild.id}`) | User: `{message.author!s}` (`{message.author.id}`)\nContent: `{message.content}`")


def setup(bot:CustomBot):
    x = CommandEvent(bot)
    bot.add_cog(x)
