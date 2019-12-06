from datetime import datetime as dt
import asyncio
import json

import discord

from cogs import utils


class RedisHandler(utils.Cog):
    """A cog to handle all of the redis message recieves"""

    DEFAULT_EV_MESSAGE = "return 'Message not received'"

    def __init__(self, bot:utils.CustomBot):
        super().__init__(bot)
        self._channels = []  # Populated automatically

        # Set up our redis handlers baybee
        task = bot.loop.create_task
        self.handlers = [
            task(self.channel_handler('DBLVote', lambda data: bot.dbl_votes.__setitem__(data['user_id'], dt.strptime(data['datetime'], "%Y-%m-%dT%H:%M:%S.%f")))),
            task(self.channel_handler('ProposalCacheAdd', lambda data: bot.proposal_cache.raw_add(**data))),
            task(self.channel_handler('ProposalCacheRemove', lambda data: bot.proposal_cache.raw_remove(*data))),
            task(self.channel_handler('EvalAll', self.eval_all)),
        ]
        # if not self.bot.is_server_specific:
        self.handlers.extend([
            task(self.channel_handler('TreeMemberUpdate', lambda data: utils.FamilyTreeMember(**data))),
        ])

    def cog_unload(self):
        """Handles cancelling all the channel subscriptions on cog unload"""

        for handler in self.handlers:
            handler.cancel()
        for channel in self._channels.copy():
            self.bot.loop.run_until_complete(self.bot.redis.pool.unsubscribe(channel))
            self._channels.remove(channel)
            self.log_handler.info(f"Unsubscribing from Redis channel {channel}")

    async def channel_handler(self, channel_name:str, function:callable, *args, **kwargs):
        """General handler for creating a channel, waiting for an input, and then plugging the
        data into a function"""

        # Subscribe to the given channel
        self._channels.append(channel_name)
        async with self.bot.redis() as re:
            self.log_handler.info(f"Subscribing to Redis channel {channel_name}")
            channel_list = await re.conn.subscribe(channel_name)

        # Get the channel from the list, loop it forever
        channel = channel_list[0]
        self.log_handler.info(f"Looping to wait for messages to channel {channel_name}")
        while (await channel.wait_message()):
            data = await channel.get_json()
            self.bot.redis.logger.debug(f"Received JSON at channel {channel_name}:{json.dumps(data)}")
            if asyncio.iscoroutine(function) or asyncio.iscoroutinefunction(function):
                await function(data, *args, **kwargs)
            else:
                function(data, *args, **kwargs)

    async def eval_all(self, data:dict):
        """Creates a context object to go through and be invoked under the .ev command"""

        # Make sure to not run it again
        if self.bot.shard_ids == data['exempt']:
            self.log_handler.info("Not invoking Redis received evall with reason exemption")
            return

        # Get message
        channel: discord.TextChannel = self.bot.get_channel(data['channel_id']) or await self.bot.fetch_channel(data['channel_id'])
        message: discord.Message = await channel.fetch_message(data['message_id'])
        content = f"{self.bot.config['prefix']['default_prefix']}ev {data.get('content', self.DEFAULT_EV_MESSAGE)}"
        message._handle_content(content)

        # Invoke command
        self.log_handler.info(7)
        ctx: utils.Context = await self.bot.get_context(message, cls=utils.Context)
        ctx.invoked_with = 'ev'
        self.log_handler.info(f"Invoking evall - {content}")
        await ctx.command.invoke(ctx)


def setup(bot:utils.CustomBot):
    x = RedisHandler(bot)
    bot.add_cog(x)
