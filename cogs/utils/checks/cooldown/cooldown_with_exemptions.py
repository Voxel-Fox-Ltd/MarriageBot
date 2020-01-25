from discord.ext import commands

from cogs.utils.checks.cooldown import Cooldown


class CooldownWithChannelExemptions(Cooldown):
    """A custom cooldown which allows for channel white/blacklisting

    Params:
        cooldown_in : typing.List[str]
            A list of channel names where the cooldown should apply
            If left blank, it'll apply everywhere minus the blacklist given
        no_cooldown_in : typing.List[str]
            A list of channel names where the cooldown shouldn't apply
            If left blank, it won't apply anywhere apart from the whitelist
    """

    _copy_kwargs = ('cooldown_in', 'no_cooldown_in')

    def __init__(self, *, cooldown_in:list=None, no_cooldown_in:list=None, **kwargs):
        """Store our nice ol lists of things"""

        super().__init__(**kwargs)
        if cooldown_in is None and no_cooldown_in is None:
            raise ValueError("You need to set at least one channel in your blacklist/whitelist")
        self.cooldown_in = cooldown_in or []
        self.no_cooldown_in = no_cooldown_in or []

    def __call__(self, rate, per, type=None):
        super().__call__(rate, per, commands.BucketType.channel)  # Override cooldown type

    def predicate(self, message) -> bool:
        """The check to see if this cooldown is applied"""

        if self.no_cooldown_in:
            if any([i for i in self.no_cooldown_in if i == message.channel.name]):
                return False
        if self.cooldown_in:
            if not any([i for i in self.cooldown_in if i == message.channel.name]):
                return False
        return True
