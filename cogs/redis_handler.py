from __future__ import annotations

import discord
from discord.ext import vbu

from cogs import utils


class RedisHandler(vbu.Cog[utils.types.Bot]):

    def __init__(self, bot):
        super().__init__(bot)
        if vbu.RedisConnection.enabled:
            self.update_guild_prefix.start()
            self.update_max_family_members.start()
            self.update_incest_alllowed.start()
            self.update_max_children.start()
            self.update_gifs_enabled.start()
            self.send_user_message.start()
            self.tree_member_update.start()

    def cog_unload(self):
        self.update_guild_prefix.stop()
        self.update_max_family_members.stop()
        self.update_incest_alllowed.stop()
        self.update_max_children.stop()
        self.update_gifs_enabled.stop()
        self.send_user_message.stop()
        self.tree_member_update.stop()

    @vbu.redis_channel_handler("UpdateGuildPrefix")
    def update_guild_prefix(self, payload: utils.types.GuildPrefixPayload):
        """
        Updates the prefix for the guild.
        """

        self.bot.guild_settings[payload['guild_id']].update(payload)  # type: ignore - missing additional keys

    @vbu.redis_channel_handler("UpdateFamilyMaxMembers")
    def update_max_family_members(self, payload: utils.types.FamilyMaxMembersPayload):
        """
        Updates the max number of family members for the guild.
        """

        data = payload.get('max_family_members')
        self.bot.guild_settings[payload['guild_id']]['max_family_members'] = data

    @vbu.redis_channel_handler("UpdateIncestAllowed")
    def update_incest_alllowed(self, payload: utils.types.IncestAllowedPayload):
        """
        Updates whether incest is allowed on guild.
        """

        data = payload.get('allow_incest')
        self.bot.guild_settings[payload['guild_id']]['allow_incest'] = data

    @vbu.redis_channel_handler("UpdateMaxChildren")
    def update_max_children(self, payload: utils.types.MaxChildrenPayload):
        """
        Updates the maximum children allowed per role in a guild.
        """

        data = payload.get('max_children')
        self.bot.guild_settings[payload['guild_id']]['max_children'] = data

    @vbu.redis_channel_handler("UpdateGifsEnabled")
    def update_gifs_enabled(self, payload: utils.types.GifsEnabledPayload):
        """
        Updates whether or not gifs are enabled for a guild.
        """

        data = payload.get('gifs_enabled')
        self.bot.guild_settings[payload['guild_id']]['gifs_enabled'] = data

    @vbu.redis_channel_handler("SendUserMessage")
    async def send_user_message(self, payload: utils.types.SendUserMessagePayload):
        """
        Sends a message to a given user.
        """

        if not self.bot.user:
            return
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

    @vbu.redis_channel_handler("TreeMemberUpdate")
    def tree_member_update(self, payload: utils.types.FamilyTreeMemberPayload):
        utils.FamilyTreeMember(**payload)


def setup(bot: vbu.Bot):
    x = RedisHandler(bot)
    bot.add_cog(x)
