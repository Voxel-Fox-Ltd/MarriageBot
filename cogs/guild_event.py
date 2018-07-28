from datetime import datetime
from discord import Guild, Embed
from cogs.utils.custom_bot import CustomBot


class GuildEvent(object):

    def __init__(self, bot:CustomBot):
        self.bot = bot


    @property
    def log_channel(self):
        channel_id = self.bot.config['log_channel']
        channel = self.bot.get_channel(channel_id)
        return channel    


    async def on_guild_join(self, guild:Guild):
        '''
        When the client is added to a new guild
        '''

        embed = Embed(colour=0x00ff00)
        embed.set_author(name=f'Added to Guild (#{len(self.bot.guilds)})')
        embed.add_field(name='Guild Name', value=guild.name)
        embed.add_field(name='Guild ID', value=guild.id)
        embed.add_field(name='Member Count', value=len(guild.members))
        embed.set_footer(text=datetime.now().strftime('%A, %x %X'))
        await self.log_channel.send(embed=embed)

        if len(self.bot.guilds) % 5 == 0:
            await self.bot.post_guild_count()


    async def on_guild_remove(self, guild:Guild):
        '''
        When the client is removed from a guild
        '''

        embed = Embed(colour=0xff0000)
        embed.set_author(name=f'Removed from Guild (#{len(self.bot.guilds)})')
        embed.add_field(name='Guild Name', value=guild.name)
        embed.add_field(name='Guild ID', value=guild.id)
        embed.add_field(name='Member Count', value=len(guild.members))
        embed.set_footer(text=datetime.now().strftime('%A, %x %X'))
        await self.log_channel.send(embed=embed)

        if len(self.bot.guilds) % 5 == 0:
            await self.bot.post_guild_count()


def setup(bot:CustomBot):
    x = GuildEvent(bot)
    bot.add_cog(x)
