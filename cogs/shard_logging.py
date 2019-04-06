from datetime import datetime as dt
from asyncio import sleep

from discord import Message, Guild, Member, Role, Emoji, RawMessageUpdateEvent, RawMessageDeleteEvent, RawReactionActionEvent, RawReactionClearEvent
from discord.ext.commands import Cog

from cogs.utils.custom_bot import CustomBot


class ShardLogging(Cog):

    DEFAULT_DATA = {
        'message_create': 0,
        'message_edit': 0,
        'typing_start': 0,
        'message_delete': 0,
        'reaction_add': 0,
        'reaction_remove': 0,
        'reaction_clear': 0,
        'channel_create': 0,
        'channel_delete': 0,
        'channel_update': 0,
        'member_join': 0,
        'member_remove': 0,
        'member_update': 0,
        'guild_join': 0,
        'guild_remove': 0,
        'guild_update': 0,
        'role_create': 0,
        'role_delete': 0,
        'role_update': 0,
        'emoji_update': 0,
        'voice_state_update': 0,
        'member_ban': 0,
        'member_unban': 0,
    }

    def __init__(self, bot:CustomBot):
        self.bot = bot
        self.data = {}
        self.logger = self.bot.loop.create_task(self.run_logger())


    def increment(self, shard_id:int, event:str):
        '''Increments the counter on a particular event'''

        data = self.data.get(shard_id, self.DEFAULT_DATA.copy())
        data[event] += 1 
        self.data[shard_id] = data


    def cog_unload(self):
        self.logger.cancel()
        self.bot.loop.run_until_complete(self.log_cache())


    async def run_logger(self):
        '''
        Runs the logger loop that stores the commands
        '''

        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            await sleep(60)
            await self.log_cache()


    async def log_cache(self):
        '''
        Runs the loop to log the shard data to the database
        '''

        COLUMNS = ['message_create', 'message_edit', 'typing_start', 'message_delete', 'reaction_add', 'reaction_remove', 'reaction_clear', 'channel_create', 'channel_delete', 'channel_update', 'member_join', 'member_remove', 'member_update', 'guild_join', 'guild_remove', 'guild_update', 'role_create', 'role_delete', 'role_update', 'emoji_update', 'voice_state_update', 'member_ban', 'member_unban', 'shard_id', 'timestamp', 'latency']
        data = self.data.copy() 
        self.data.clear()

        # Put data in list form
        list_data = [(
            o['message_create'],
            o['message_edit'],
            o['typing_start'],
            o['message_delete'],
            o['reaction_add'],
            o['reaction_remove'],
            o['reaction_clear'],
            o['channel_create'],
            o['channel_delete'],
            o['channel_update'],
            o['member_join'],
            o['member_remove'],
            o['member_update'],
            o['guild_join'],
            o['guild_remove'],
            o['guild_update'],
            o['role_create'],
            o['role_delete'],
            o['role_update'],
            o['emoji_update'],
            o['voice_state_update'],
            o['member_ban'],
            o['member_unban'],
            i,
            dt.now(),
            self.bot.latencies[i][1] * 1000
        ) for i, o in data.items()]

        # Post to database
        async with self.bot.database() as db:
            await db.conn.copy_records_to_table(
                'shard_logging', 
                records=list_data,
                columns=COLUMNS
            )


    @Cog.listener()
    async def on_message(self, message:Message):
        '''Triggers when a message is sent'''

        guild = message.guild
        if not guild: shard_id = 0 
        else: shard_id = guild.shard_id
        self.increment(shard_id, 'message_create')


    @Cog.listener()
    async def on_raw_message_edit(self, payload:RawMessageUpdateEvent):
        '''Triggers when a message is edited'''

        try: guild = self.bot.get_guild(payload.data['guild_id'])
        except KeyError: guild = None
        if not guild: shard_id = 0 
        else: shard_id = guild.shard_id
        self.increment(shard_id, 'message_edit')


    @Cog.listener()
    async def on_typing(self, channel, user, when):
        '''Triggers when a user or member starts typing'''

        try: shard_id = user.guild.shard_id
        except AttributeError: shard_id = 0
        self.increment(shard_id, 'typing_start')


    @Cog.listener()
    async def on_raw_message_delete(self, payload:RawMessageDeleteEvent):
        '''Triggers when a message is deleted'''
        
        guild = self.bot.get_guild(payload.guild_id)
        if not guild: shard_id = 0 
        else: shard_id = guild.shard_id
        self.increment(shard_id, 'message_delete')


    @Cog.listener()
    async def on_raw_reaction_clear(self, payload:RawReactionClearEvent):
        '''Triggers when reactions are cleared from a message'''

        guild = self.bot.get_guild(payload.guild_id)
        if not guild: shard_id = 0 
        else: shard_id = guild.shard_id
        self.increment(shard_id, 'reaction_clear')


    @Cog.listener()
    async def on_raw_reaction_remove(self, payload:RawReactionActionEvent):
        '''Triggers when a reaction is removed from a message'''

        guild = self.bot.get_guild(payload.guild_id)
        if not guild: shard_id = 0 
        else: shard_id = guild.shard_id
        self.increment(shard_id, 'reaction_remove')


    @Cog.listener()
    async def on_raw_reaction_add(self, payload:RawReactionActionEvent):
        '''Triggers when a reaction is added to a message'''

        guild = self.bot.get_guild(payload.guild_id)
        if not guild: shard_id = 0 
        else: shard_id = guild.shard_id
        self.increment(shard_id, 'reaction_add')


    @Cog.listener()
    async def on_guild_channel_create(self, channel):
        '''Triggers when a channel is created in a guild'''

        self.increment(channel.guild.shard_id, 'channel_create')


    @Cog.listener()
    async def on_guild_channel_delete(self, channel):
        '''Triggers when a channel is deleted from a guild'''

        self.increment(channel.guild.shard_id, 'channel_delete')


    @Cog.listener()
    async def on_guild_channel_update(self, before, after):
        '''Triggers when a channel is updated'''

        self.increment(after.guild.shard_id, 'channel_update')


    @Cog.listener()
    async def on_member_join(self, member:Member):
        '''Triggers when a member joins a guild'''

        self.increment(member.guild.shard_id, 'member_join')


    @Cog.listener()
    async def on_member_remove(self, member:Member):
        '''Triggers when a member is removed from a guild'''

        self.increment(member.guild.shard_id, 'member_remove')


    @Cog.listener()
    async def on_member_update(self, before:Member, after:Member):
        '''Triggers when a member is removed from a guild'''

        self.increment(after.guild.shard_id, 'member_update')


    @Cog.listener()
    async def on_guild_join(self, guild:Guild):
        '''Triggers when the bot joins a guild'''

        self.increment(guild.shard_id, 'guild_join')


    @Cog.listener()
    async def on_guild_remove(self, guild:Guild):
        '''Triggers when the bot is removed from a guild'''

        self.increment(guild.shard_id, 'guild_remove')


    @Cog.listener()
    async def on_guild_update(self, before:Guild, after:Guild):
        '''Triggers when a guild updates its settings'''

        self.increment(after.shard_id, 'guild_update')


    @Cog.listener()
    async def on_role_create(self, role:Role):
        '''Triggers when a guild creates a role'''

        self.increment(role.guild.shard_id, 'role_create')


    @Cog.listener()
    async def on_role_delete(self, role:Role):
        '''Triggers when a guild deletes a role'''

        self.increment(role.guild.shard_id, 'role_delete')


    @Cog.listener()
    async def on_role_udpate(self, role:Role):
        '''Triggers when a guild udpates a role'''

        self.increment(role.guild.shard_id, 'role_udpate')


    @Cog.listener()
    async def on_emoji_update(self, emoji:Emoji):
        '''Triggers when a guild adds/removes/updates an emoji'''

        self.increment(emoji.guild.shard_id, 'emoji_update')


    @Cog.listener()
    async def on_voice_state_update(self, member:Member, before, after):
        '''Triggers when a user updates their voice state in a guild'''

        self.increment(member.guild.shard_id, 'voice_state_update')


    @Cog.listener()
    async def on_member_ban(self, guild:Guild, user):
        '''Triggers when a user is banned from a guild'''

        self.increment(guild.shard_id, 'member_ban')


    @Cog.listener()
    async def on_member_unban(self, guild:Guild, user):
        '''Triggers when a user is unbanned from a guild'''

        self.increment(guild.shard_id, 'member_unban')


def setup(bot:CustomBot):
    x = ShardLogging(bot)
    bot.add_cog(x)
