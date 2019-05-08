from datetime import datetime as dt
from asyncio import iscoroutinefunction, iscoroutine

from cogs.utils.custom_cog import Cog
from cogs.utils.custom_context import NoOutputContext, CustomContext
from cogs.utils.custom_bot import CustomBot
from cogs.utils.family_tree.family_tree_member import FamilyTreeMember


class RedisHandler(Cog):

    def __init__(self, bot:CustomBot):
        self.bot = bot 
        super().__init__(__class__.__name__)
        task = bot.loop.create_task
        self.channels = []  # Populated automatically
        self.handlers = [
            task(self.channel_handler('TreeMemberUpdate', lambda data: FamilyTreeMember(**data))),
            task(self.channel_handler('RunGlobalCommand', self.run_global_command)),
            task(self.channel_handler('ProposalCacheAdd', lambda data: bot.proposal_cache.raw_add(**data))),
            task(self.channel_handler('ProposalCacheRemove', lambda data: bot.proposal_cache.raw_remove(*data))),
            task(self.channel_handler('TreeCacheAdd', lambda data: bot.tree_cache.raw_add(*data))),
            task(self.channel_handler('TreeCacheRemove', lambda data: bot.tree_cache.raw_remove(*data))),
            task(self.channel_handler('DBLVote', lambda data: bot.dbl_votes.__setitem__(data['user_id'], dt.strptime(data['datetime'], "%Y-%m-%dT%H:%M:%S.%f")))),
        ]


    def cog_unload(self):
        for handler in self.handlers:
            handler.cancel()
        for channel in self.channels.copy():
            self.bot.loop.run_until_complete(self.bot.redis.pool.unsubscribe(channel))
            self.channels.remove(channel)


    async def channel_handler(self, channel_name:str, function:callable):
        '''
        General handler for creating a channel, waiting for an input, and then 
        plugging the data into a function
        '''

        # Subscribe to the given channel
        self.channels.append(channel_name)
        async with self.bot.redis() as re:
            self.log_handler.debug(f"Subscribing to Redis channel {channel_name}")
            channel_list = await re.conn.subscribe(channel_name)

        # Get the channel from the list, loop it forever
        channel = channel_list[0]
        self.log_handler.debug(f"Looping to wait for messages to channel {channel_name}")
        while (await channel.wait_message()):

            # Get and log the data
            data = await channel.get_json()
            self.log_handler.debug(f"Redis message on {channel_name}: {data!s}")
            
            # Run the callable
            if iscoroutine(function) or iscoroutinefunction(function):
                await function(data)
            else:
                function(data)

        
    async def run_global_command(self, data:dict):
        '''Runs a given command globally, across all shards'''

        # Get guild
        self.log_handler.debug(f"Running global command with content '{data['command']}'")
        guild_id = data['guild_id']
        guild = self.bot.get_guild(guild_id)
        if not guild:
            guild = await self.bot.fetch_guild(guild_id)

        # Get channel
        channel = guild.get_channel(data['channel_id'])

        # Get message
        message = await channel.fetch_message(data['message_id'])

        # Change message content
        message.content = data['command']

        # Invoke command
        if guild.shard_id in self.bot.shard_ids:
            ctx = self.bot.get_context(message, cls=CustomContext)
        else:
            ctx = self.bot.get_context(message, cls=NoOutputContext)
        self.log_handler.debug('Invoking context')
        await self.bot.invoke(ctx)


def setup(bot:CustomBot):
    x = RedisHandler(bot)
    bot.add_cog(x)
