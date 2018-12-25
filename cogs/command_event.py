from asyncio import sleep

from discord import Message, Embed
from discord.ext.commands import Context

from cogs.utils.custom_bot import CustomBot


class CommandEvent(object):

    def __init__(self, bot:CustomBot):
        self.bot = bot
        self.cache = []


    @property
    def command_log_channel(self):
        channel_id = self.bot.config['command_log_channel']
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

        if not self.command_log_channel:
            return

        if ctx.guild:
            await self.command_log_channel.send(f"Guild: `{ctx.guild.name}` (`{ctx.guild.id}`) | Channel: `{ctx.channel.name}` (`{ctx.channel.id}`) | User: `{ctx.author!s}` (`{ctx.author.id}`)\nMessage (`{ctx.message.id}`) Content: `{ctx.message.content}`")
        else:
            await self.command_log_channel.send(f"Guild: `{ctx.guild}` (`{ctx.guild}`) | Channel: `{ctx.channel}` (`{ctx.channel}`) | User: `{ctx.author!s}` (`{ctx.author.id}`)\nMessage (`{ctx.message.id}`) Content: `{ctx.message.content}`")
        self.cache.append(ctx.message)


    async def on_message(self, message:Message):
        '''
        Runs to log any time anyone says "marriagebot"
        '''

        if not self.chat_channel:
            return

        if message.guild == None:
            text = f"""Guild: `{message.guild}`
                    User: `{message.author!s}` (`{message.author.id}`)
                    Correspondant: `{message.channel.recipient}` (`{message.channel.recipient.id}`)
                    Message (`{message.id}`)""".replace('\t'*5, '').replace(' '*5*4, '')
        elif message.author.bot:
            return
        elif any([i in message.content.casefold() for i in ['marriagebot', 'marriage bot', f'{self.bot.user.id}']]):
            await sleep(0.1)
            if message in self.cache:
                self.cache.remove(message)
                return
            text = f"""Guild: `{message.guild.name}` (`{message.guild.id}`)
                    Channel: `{message.channel.name}` (`{message.channel.id}`)
                    User: `{message.author!s}` (`{message.author.id}`)
                    Message (`{message.id}`)""".replace('\t'*5, '').replace(' '*5*4, '')
        else:
            return
        attachments = [i.url for i in message.attachments]
        if attachments:
            text += '\nAttachments: ' + ', '.join(attachments)
        
        # Construct the embed
        if message.author.guild:
            embed = Embed(colour=message.author.top_role.colour.value)
        else:
            embed = Embed()
        embed.set_author(name=message.author, icon_url=message.author.avatar_url) 
        embed.description = message.clean_content
        await self.chat_channel.send(text, embed=embed)         


def setup(bot:CustomBot):
    x = CommandEvent(bot)
    bot.add_cog(x)
