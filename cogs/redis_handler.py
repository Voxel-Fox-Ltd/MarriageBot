from datetime import datetime as dt

import discord
import voxelbotutils

from cogs import utils as localutils


class RedisHandler(voxelbotutils.Cog):

    def __init__(self, bot:voxelbotutils.Bot):
        super().__init__(bot)
        self.update_guild_prefix.start()
        self.update_max_family_members.start()
        self.update_incest_alllowed.start()
        self.update_max_children.start()
        self.update_gifs_enabled.start()
        self.send_user_message.start()
        self.redis_handler_ProposalCacheAdd.start()
        self.redis_handler_ProposalCacheRemove.start()
        self.redis_handler_TreeMemberUpdate.start()

    def cog_unload(self):
        self.update_guild_prefix.stop()
        self.update_max_family_members.stop()
        self.update_incest_alllowed.stop()
        self.update_max_children.stop()
        self.update_gifs_enabled.stop()
        self.send_user_message.stop()
        self.redis_handler_ProposalCacheAdd.stop()
        self.redis_handler_ProposalCacheRemove.stop()
        self.redis_handler_TreeMemberUpdate.stop()

    @voxelbotutils.redis_channel_handler("UpdateGuildPrefix")
    def update_guild_prefix(self, payload):
        """
        Updates the prefix for the guild.
        """

        key = self.bot.config['guild_settings_prefix_column']
        data = payload.get(key)
        self.bot.guild_settings[payload['guild_id']][key] = data

    @voxelbotutils.redis_channel_handler("UpdateFamilyMaxMembers")
    def update_max_family_members(self, payload):
        """
        Updates the max number of family members for the guild.
        """

        data = payload.get('max_family_members')
        self.bot.guild_settings[payload['guild_id']]['max_family_members'] = data

    @voxelbotutils.redis_channel_handler("UpdateIncestAllowed")
    def update_incest_alllowed(self, payload):
        """
        Updates whether incest is allowed on guild.
        """

        data = payload.get('allow_incest')
        self.bot.guild_settings[payload['guild_id']]['allow_incest'] = data

    @voxelbotutils.redis_channel_handler("UpdateMaxChildren")
    def update_max_children(self, payload):
        """
        Updates the maximum children allowed per role in a guild.
        """

        data = payload.get('max_children')
        self.bot.guild_settings[payload['guild_id']]['max_children'] = data

    @voxelbotutils.redis_channel_handler("UpdateGifsEnabled")
    def update_gifs_enabled(self, payload):
        """
        Updates whether or not gifs are enabled for a guild.
        """

        data = payload.get('gifs_enabled')
        self.bot.guild_settings[payload['guild_id']]['gifs_enabled'] = data

    @voxelbotutils.redis_channel_handler("SendUserMessage")
    async def send_user_message(self, payload):
        """
        Sends a message to a given user.
        """

        if self.bot.user.id != payload.get('bot_id', None):
            return
        if 0 not in (self.bot.shard_ids or [0]):
            pass
        try:
            user = await self.bot.fetch_user(payload['user_id'])
            await user.send(payload['content'])
            self.logger.info(f"Sent a DM to user ID {payload['user_id']}")
        except (discord.NotFound, discord.Forbidden, AttributeError):
            pass

    @voxelbotutils.redis_channel_handler("ProposalCacheAdd")
    def redis_handler_ProposalCacheAdd(self, payload):
        self.bot.proposal_cache.raw_add(**payload)

    @voxelbotutils.redis_channel_handler("ProposalCacheRemove")
    def redis_handler_ProposalCacheRemove(self, payload):
        self.bot.proposal_cache.raw_remove(*payload)

    @voxelbotutils.redis_channel_handler("TreeMemberUpdate")
    def redis_handler_TreeMemberUpdate(self, payload):
        localutils.FamilyTreeMember(**payload)


def setup(bot:voxelbotutils.Bot):
    x = RedisHandler(bot)
    bot.add_cog(x)
