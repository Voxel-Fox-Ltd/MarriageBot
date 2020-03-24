import discord
from discord.ext import commands

from cogs.utils.checks.cooldown.cooldown import Cooldown, CooldownMapping


class RoleBasedCooldown(Cooldown):

    tier_cooldowns = {
        1: 60,
        2: 60 * 2,
        3: 60 * 3,
        4: 60 * 4,
        5: 60 * 5,
    }  # RoleID: CooldownSeconds

    _copy_kwargs = ()

    def predicate(self, message:discord.Message):
        """Update the cooldown based on the given guild member"""

        if message.guild is None:
            return  # Go for the default
        cooldown_seconds = [o for i, o in self.tier_cooldowns.items() if i in message.author._roles]  # Get valid cooldowns
        if not cooldown_seconds:
            return
        self.per = min(cooldown_seconds)  # Set this rate as the minimum form the roles
