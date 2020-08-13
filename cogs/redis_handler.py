import asyncio
import json
from datetime import datetime as dt

import discord

from cogs import utils


class RedisHandler(utils.Cog):

    DEFAULT_EV_MESSAGE = "return 'Message not received'"

    def __init__(self, bot:utils.Bot):
        super().__init__(bot)
        self._channels = []  # Populated automatically

        # Set up our redis handlers baybee
        task = bot.loop.create_task
        self.handlers = [
            task(self.channel_handler('DBLVote', lambda data: bot.dbl_votes.__setitem__(data['user_id'], dt.strptime(data['datetime'], "%Y-%m-%dT%H:%M:%S.%f")))),
            task(self.channel_handler('ProposalCacheAdd', lambda data: bot.proposal_cache.raw_add(**data))),
            task(self.channel_handler('ProposalCacheRemove', lambda data: bot.proposal_cache.raw_remove(*data))),
            task(self.channel_handler('BlockedUserAdd', lambda data: bot.blocked_users[data['user_id']].append(data['blocked_user_id']))),
            task(self.channel_handler('BlockedUserRemove', lambda data: bot.blocked_users[data['user_id']].remove(data['blocked_user_id']))),
            task(self.channel_handler('EvalAll', self.eval_all)),
            task(self.channel_handler('UpdateGuildPrefix', self.update_guild_prefix)),
            task(self.channel_handler('UpdateFamilyMaxMembers', self.update_max_family_members)),
            task(self.channel_handler('UpdateIncestAllowed', self.update_incest_alllowed)),
            task(self.channel_handler('UpdateMaxChildren', self.update_max_children)),
            task(self.channel_handler('UpdateGifsEnabled', self.update_gifs_enabled)),
            task(self.channel_handler('SendUserMessage', self.send_user_message)),
            task(self.channel_handler('AddGoldUser', self.add_gold_user)),
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
            asyncio.ensure_future(asyncio.wait_for(self.bot.redis.pool.unsubscribe(channel), timeout=None), loop=self.bot.loop)
            self._channels.remove(channel)
            self.logger.info(f"Unsubscribing from Redis channel {channel}")

    async def channel_handler(self, channel_name:str, function:callable, *args, **kwargs):
        """General handler for creating a channel, waiting for an input, and then plugging the
        data into a function"""

        # Subscribe to the given channel
        self._channels.append(channel_name)
        async with self.bot.redis() as re:
            self.logger.info(f"Subscribing to Redis channel {channel_name}")
            channel_list = await re.conn.subscribe(channel_name)

        # Get the channel from the list, loop it forever
        channel = channel_list[0]
        self.logger.info(f"Looping to wait for messages to channel {channel_name}")
        while (await channel.wait_message()):
            data = await channel.get_json()
            self.bot.redis.logger.debug(f"Received JSON at channel {channel_name}:{json.dumps(data)}")
            try:
                if asyncio.iscoroutine(function) or asyncio.iscoroutinefunction(function):
                    await function(data, *args, **kwargs)
                else:
                    function(data, *args, **kwargs)
            except Exception as e:
                self.logger.error(e)

    async def eval_all(self, data:dict):
        """Creates a context object to go through and be invoked under the .ev command"""

        # Make sure to not run it again
        if self.bot.shard_ids == data['exempt']:
            self.logger.info("Not invoking Redis received evall with reason exemption")
            return

        # Get message
        channel: discord.TextChannel = await self.bot.fetch_channel(data['channel_id'])
        channel.guild = await self.bot.fetch_guild(channel.guild.id)
        message: discord.Message = await channel.fetch_message(data['message_id'])
        message.author = await channel.guild.fetch_member(data['author_id'])
        ev_content = data.get('content', self.DEFAULT_EV_MESSAGE)
        message.content = f"<@{self.bot.user.id}> {ev_content}"

        # Invoke command
        ctx: utils.Context = await self.bot.get_context(message, cls=utils.Context)
        ctx.command = self.bot.get_command('ev')
        ctx.invoked_with = 'ev'
        ctx.prefix = f'<@{self.bot.user.id}>'
        ctx.include_shards = True
        self.logger.info(f"Invoking evall - {message.content}")
        try:
            await ctx.invoke(ctx.command, content=ev_content.split(' ', 1)[1])
        except Exception as e:
            self.logger.exception(e)
            raise e

    def update_guild_prefix(self, data):
        """Updates the prefix for the guild"""

        if self.bot.is_server_specific:
            key = "gold_prefix"
        else:
            key = "prefix"
        prefix = data.get(key)
        if prefix is None:
            return
        self.bot.guild_settings[data['guild_id']]['prefix'] = prefix

    def update_max_family_members(self, data):
        """Updates the max number of family members for the guild"""

        prefix = data.get('max_family_members')
        if prefix is None:
            return
        self.bot.guild_settings[data['guild_id']]['max_family_members'] = prefix

    def update_incest_alllowed(self, data):
        """Updates whether incest is allowed on guild"""

        prefix = data.get('allow_incest')
        if prefix is None:
            return
        self.bot.guild_settings[data['guild_id']]['allow_incest'] = prefix

    def update_max_children(self, data):
        """Updates the maximum children allowed per role in a guild"""

        prefix = data.get('max_children')
        if prefix is None:
            return
        self.bot.guild_settings[data['guild_id']]['max_children'] = prefix

    def update_gifs_enabled(self, data):
        """Updates whether or not gifs are enabled for a guild"""

        prefix = data.get('gifs_enabled')
        if prefix is None:
            return
        self.bot.guild_settings[data['guild_id']]['gifs_enabled'] = prefix

    async def send_user_message(self, data):
        """Sends a message to a given user"""

        if self.bot.shards is None or 0 in self.bot.shard_ids:
            pass
        else:
            return
        try:
            user = await self.bot.fetch_user(data['user_id'])
            await user.send(data['content'])
            self.logger.info(f"Sent a DM to user ID {data['user_id']}")
        except (discord.NotFound, discord.Forbidden, AttributeError):
            pass

    async def add_gold_user(self, data):
        """Sends a message to a given user"""

        if self.bot.shard_ids is None or 0 in self.bot.shard_ids:
            pass
        else:
            return
        try:
            await self.bot.fetch_support_guild()
            guild = self.bot.support_guild
            member = await guild.fetch_member(data['user_id'])
            roles = []
            self.logger.info("Adding Patreon roles to gold user")
            for role_id in [self.bot.config['guild_specific_role']]:
                roles.append(guild.get_role(role_id))
            await member.add_roles(*roles, reason='MarriageBot Gold purchase')
            self.logger.info("Added donation roles to gold user")
        except Exception as e:
            self.logger.error(e)
            pass


def setup(bot:utils.Bot):
    x = RedisHandler(bot)
    bot.add_cog(x)
