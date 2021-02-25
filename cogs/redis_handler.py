from datetime import datetime as dt

import discord
import voxelbotutils as utils

from cogs import utils as localutils


class RedisHandler(utils.Cog):

    @utils.redis_channel_handler("UpdateGuildPrefix")
    def update_guild_prefix(self, data):
        """
        Updates the prefix for the guild.
        """

        key = self.bot.config['guild_settings_prefix_column']
        data = data.get(key)
        self.bot.guild_settings[data['guild_id']][key] = data

    @utils.redis_channel_handler("UpdateFamilyMaxMembers")
    def update_max_family_members(self, data):
        """
        Updates the max number of family members for the guild.
        """

        data = data.get('max_family_members')
        self.bot.guild_settings[data['guild_id']]['max_family_members'] = data

    @utils.redis_channel_handler("UpdateIncestAllowed")
    def update_incest_alllowed(self, data):
        """
        Updates whether incest is allowed on guild.
        """

        data = data.get('allow_incest')
        self.bot.guild_settings[data['guild_id']]['allow_incest'] = data

    @utils.redis_channel_handler("UpdateMaxChildren")
    def update_max_children(self, data):
        """
        Updates the maximum children allowed per role in a guild.
        """

        prefix = data.get('max_children')
        if prefix is None:
            return
        self.bot.guild_settings[data['guild_id']]['max_children'] = prefix

    @utils.redis_channel_handler("UpdateGifsEnabled")
    def update_gifs_enabled(self, data):
        """
        Updates whether or not gifs are enabled for a guild.
        """

        prefix = data.get('gifs_enabled')
        if prefix is None:
            return
        self.bot.guild_settings[data['guild_id']]['gifs_enabled'] = prefix

    @utils.redis_channel_handler("SendUserMessage")
    async def send_user_message(self, data):
        """
        Sends a message to a given user.
        """

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

    @utils.redis_channel_handler("DBLVote")
    def redis_handler_DBLVote(self, data):
        self.bot.dbl_votes.__setitem__(data['user_id'], dt.strptime(data['datetime'], "%Y-%m-%dT%H:%M:%S.%f"))

    @utils.redis_channel_handler("ProposalCacheAdd")
    def redis_handler_ProposalCacheAdd(self, data):
        self.bot.proposal_cache.raw_add(**data)

    @utils.redis_channel_handler("ProposalCacheRemove")
    def redis_handler_ProposalCacheRemove(self, data):
        self.bot.proposal_cache.raw_remove(*data)

    @utils.redis_channel_handler("TreeMemberUpdate")
    def redis_handler_TreeMemberUpdate(self, data):
        localutils.FamilyTreeMember(**data)


def setup(bot:utils.Bot):
    x = RedisHandler(bot)
    bot.add_cog(x)
