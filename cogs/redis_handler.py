from datetime import datetime as dt
from asyncio import iscoroutinefunction, iscoroutine

from cogs.utils.custom_cog import Cog
from cogs.utils.custom_context import NoOutputContext, CustomContext
from cogs.utils.custom_bot import CustomBot
from cogs.utils.family_tree.family_tree_member import FamilyTreeMember


class RedisHandler(Cog):
    """A cog to handle all of the redis message recieves"""

    def __init__(self, bot:CustomBot):
        self.bot = bot
        super().__init__(__class__.__name__)
        task = bot.loop.create_task

        self.channels = []  # Populated automatically
        self.handlers = [
            task(self.channel_handler('DBLVote', lambda data: bot.dbl_votes.__setitem__(data['user_id'], dt.strptime(data['datetime'], "%Y-%m-%dT%H:%M:%S.%f")))),
            task(self.channel_handler('UpdateGuildPrefix', self.set_prefix)),
            task(self.channel_handler('ProposalCacheAdd', lambda data: bot.proposal_cache.raw_add(**data))),
            task(self.channel_handler('ProposalCacheRemove', lambda data: bot.proposal_cache.raw_remove(*data))),
        ]
        if not self.bot.is_server_specific:
            self.handlers.extend([
                task(self.channel_handler('TreeMemberUpdate', lambda data: FamilyTreeMember(**data))),
            ])

    def cog_unload(self):
        """Handles cancelling all the channel subscriptions on cog unload"""

        for handler in self.handlers:
            handler.cancel()
        for channel in self.channels.copy():
            self.bot.loop.run_until_complete(self.bot.redis.pool.unsubscribe(channel))
            self.channels.remove(channel)

    async def channel_handler(self, channel_name:str, function:callable, log:bool=True, *args, **kwargs):
        """General handler for creating a channel, waiting for an input, and then plugging the 
        data into a function"""

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
            if log: self.log_handler.debug(f"Redis message on {channel_name}: {data!s}")

            # Run the callable
            if iscoroutine(function) or iscoroutinefunction(function):
                await function(data, *args, **kwargs)
            else:
                function(data, *args, **kwargs)

    def set_prefix(self, data):
        """Caches a prefix for a guild"""

        try:
            self.bot.guild_prefixes[data['guild_id']] = data['prefix']
        except KeyError:
            self.bot.guild_prefixes[data['guild_id']] = {
                'prefix': data['prefix'],
                'allow_incest': False
            }


def setup(bot:CustomBot):
    x = RedisHandler(bot)
    bot.add_cog(x)
