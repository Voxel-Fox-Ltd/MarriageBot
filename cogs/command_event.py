from asyncio import sleep
from discord import Message
from discord.ext.commands import Context
from cogs.utils.custom_bot import CustomBot


class CommandEvent(object):

    def __init__(self, bot:CustomBot):
        self.bot = bot
        self.cache = []


    @property
    def log_channel(self):
        channel_id = self.bot.config['log_channel']
        channel = self.bot.get_channel(channel_id)
        return channel


    @property
    def chat_channel(self):
        channel_id = self.bot.config['chat_channel']
        channel = self.bot.get_channel(channel_id)
        return channel


    async def on_command(self, ctx:Context):
        '''
        Runs when a command is run
        '''

        if not self.log_channel:
            return

        if ctx.guild:
            await self.log_channel.send(f"Guild: `{ctx.guild.name}` (`{ctx.guild.id}`) | Channel: `{ctx.channel.name}` (`{ctx.channel.id}`) | User: `{ctx.author!s}` (`{ctx.author.id}`)\nContent: `{ctx.message.content}`")
        else:
            await self.log_channel.send(f"Guild: `{ctx.guild}` (`{ctx.guild}`) | Channel: `{ctx.channel}` (`{ctx.channel}`) | User: `{ctx.author!s}` (`{ctx.author.id}`)\nContent: `{ctx.message.content}`")
        self.cache.append(ctx.message)


    async def on_message(self, message:Message):
        '''
        Runs to log any time anyone says "marriagebot"
        '''

        if not self.chat_channel:
            return

        if message.guild == None:
            await self.chat_channel.send(f"Guild: `{message.guild}` | User: `{message.author!s}` (`{message.author.id}`) | Correspondant: `{message.channel.recipient}` (`{message.channel.recipient.id}`)\nContent: `{message.content}`")
        elif message.author.bot:
            return
        elif any([i in message.content.casefold() for i in ['marriagebot', 'marriage bot', f'{self.bot.user.id}']]):
            await sleep(1)
            if message in self.cache:
                self.cache.remove(message)
                return
            await self.chat_channel.send(f"Guild: `{message.guild.name}` (`{message.guild.id}`) | Channel: `{message.channel.name}` (`{message.channel.id}`) | User: `{message.author!s}` (`{message.author.id}`)\nContent: `{message.content}`")


def setup(bot:CustomBot):
    x = CommandEvent(bot)
    bot.add_cog(x)
