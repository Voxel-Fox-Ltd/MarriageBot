from datetime import datetime

from discord import Guild, Embed

from cogs.utils.custom_bot import CustomBot
from cogs.utils.family_tree.family_tree_member import FamilyTreeMember
from cogs.utils.custom_cog import Cog


class GuildEvent(Cog):

    def __init__(self, bot:CustomBot):
        super().__init__(self.__class__.__name__)
        self.bot = bot


    @property
    def event_log_channel(self):
        channel_id = self.bot.config['event_log_channel']
        channel = self.bot.get_channel(channel_id)
        return channel    


    @Cog.listener()
    async def on_guild_join(self, guild:Guild):
        '''
        When the client is added to a new guild
        '''

        text = f'''**Added to Guild** (`#{len(self.bot.guilds)}`)
            Guild Name: `{guild.name}`
            Guild ID: `{guild.id}`
            Member Count: `{len(guild.members)}` (Humans/Bots - `{len([i for i in guild.members if not i.bot])}`/`{len([i for i in guild.members if i.bot])}`)
            Current Datetime: `{datetime.now().strftime("%A, %x %X")}`'''.replace('\t\t\t', '').replace(' '*12, '')

        if guild.id in self.bot.blacklisted_guilds:
            text = text.replace('Added to Guild', 'Added to Blacklisted Guild')
            await guild.leave()

        try:
            await self.event_log_channel.send(text)
        except AttributeError:
            self.log_handler.error(f"Unable to send message to event_log channel: {text}")

        if len(self.bot.guilds) % 5 == 0:
            await self.bot.post_guild_count()


    @Cog.listener()
    async def on_guild_remove(self, guild:Guild):
        '''
        When the client is removed from a guild
        '''

        text = f'''**Removed from Guild** (`#{len(self.bot.guilds)}`)
            Guild Name: `{guild.name}`
            Guild ID: `{guild.id}`
            Member Count: `{len(guild.members)}` (Humans/Bots - `{len([i for i in guild.members if not i.bot])}`/`{len([i for i in guild.members if i.bot])}`)
            Current Datetime: `{datetime.now().strftime("%A, %x %X")}`'''.replace('\t\t\t', '').replace(' '*12, '')
        try:
            await self.event_log_channel.send(text)
        except AttributeError:
            self.log_handler.error(f"Unable to send message to event_log channel: {text}")

        if len(self.bot.guilds) % 5 == 0:
            await self.bot.post_guild_count()

        # Remove users from database if they were in a guild
        non_present_members = [i for i in guild.members if self.bot.get_user(i.id) == None]
        non_present_ids = [i.id for i in non_present_members]
        family_guild_members = [FamilyTreeMember.get(i) for i in non_present_ids]
        async with self.bot.database() as db:
            for i in family_guild_members:
                await db.destroy(i.id)
                i.destroy()


def setup(bot:CustomBot):
    x = GuildEvent(bot)
    bot.add_cog(x)
