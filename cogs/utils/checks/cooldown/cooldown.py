import time
import typing
import collections

import discord
from discord.ext import commands


class CooldownMapping(commands.CooldownMapping):
    """A mapping of cooldowns and who's run them, so we can keep track of individuals' rate limits

    Attrs:
        _cache : typing.Dict[int, commands.Cooldown]
            The cache for the individual and the applied cooldown
    """

    def __init__(self):
        pass

    def copy(self) -> commands.CooldownMapping:
        """Retuns a copy of the mapping, including a copy of its current cache"""

        return super().copy()

    @property
    def valid(self) -> bool:
        """Whether or not the mapping is valid"""

        return super().valid

    @classmethod
    def from_cooldown(cls, rate:float, per:int, type:commands.BucketType) -> commands.Cooldown:
        """Creates a new mapping from given cooldown params"""

        return cls(self.original.__class__(rate, per, type))

    def _bucket_key(self, message:discord.Message) -> typing.Optional[int]:
        """Gets the key for the given cooldown mapping, depending on the type of the cooldown"""

        return super()._bucket_key(message)

    def get_bucket(self, message:discord.Message, current:float=None) -> commands.Cooldown:
        """Gives you the applied cooldown for a message, which you can use to work out whether to run the command or not"""

        return super().get_bucket(message, current)

    def update_rate_limit(self, message:discord.Message, current:float=None) -> None:
        """Updates the rate limit for a given message"""

        return super().update_rate_limit(message, current)

    def __call__(self, original:commands.Cooldown):
        """Runs the original init method

        Params:
            original : commands.Cooldown
                The original cooldown that this mapping refers to
        """

        self._cooldown = original
        self._cooldown.mapping = self
        self._cache = {}
        return self


grouped_cooldown_mapping_cache = collections.defaultdict(dict)
class GroupedCooldownMapping(CooldownMapping):

    grouped_cache = grouped_cooldown_mapping_cache

    def __init__(self, key:str):
        self.group_cache_key = key

    @property
    def _cache(self):
        return grouped_cooldown_mapping_cache[self.group_cache_key]

    @_cache.setter
    def _cache(self, value):
        grouped_cooldown_mapping_cache[self.group_cache_key] = value


class Cooldown(commands.Cooldown):
    """A class handling the cooldown for an individual user

    Params:
        error : discord.ext.commands.CommandOnCooldown
            The error that should be raised when the cooldown is triggered
            Defaults to discord.ext.commands.CommandOnCooldown
        mapping: CooldownMapping
            An _instance_ of a cooldown mapping
            Will not accept the raw class object
            Defaults to cls.default_mapping_class
    Attrs:
        _window : float
            The start time (time.time(), Unix timestamp) for the cooldown
        _tokens : int
            How many more times the given command can be called in the timeframe
        _last : float
            The time (time.time(), Unix timestamp) that the command was last sucessfully called at
    """

    default_cooldown_error = commands.CommandOnCooldown
    default_mapping_class = CooldownMapping

    _copy_kwargs = ()  # The attrs that are passed into kwargs when copied; error and mapping are always copied
    __slots__ = ('rate', 'per', 'type', 'error', 'mapping', '_window', '_tokens', '_last')

    def __init__(self, *, error=None, mapping:CooldownMapping=None):
        self.error = error or commands.CommandOnCooldown
        self.mapping = mapping

    def predicate(self, message:discord.Message) -> bool:
        """Returns whether or not the cooldown should be checked to be applied or not"""

        return True

    def get_tokens(self, current:float=None) -> int:
        """Gets the number of command calls that can still be made before hitting the rate limit

        Params:
            current : float = None
                The current time, or now (via time.time())
                Is _not_ used to update self._last, since the command may not have actually been called
        Returns:
            How many more times the comman can be called before hitting the rate limit
        """

        return super().get_tokens(current)

    def update_rate_limit(self, current:float=None) -> typing.Optional[int]:
        """Updates the rate limit for the command, as it has now been called

        Params:
            current : float = None
                The current time, or now (via time.time())
        Returns:
            The amount of time left on the cooldown if there is any, else None
        """

        return super().update_rate_limit(current)

    def get_remaining_cooldown(self, current:float=None) -> typing.Optional[float]:
        """Gets the remaining rate limit for the command"""

        current = current or time.time()
        if self.get_tokens() == 0:
            return self.per - (current - self._window)
        return None

    def reset(self) -> None:
        """Resets the cooldown for the given command"""

        return super().reset()

    def copy(self) -> commands.Cooldown:
        """Returns a copy of the cooldown"""

        kwargs = {i: getattr(getattr(self, attr, None), 'copy', lambda x: x).copy() for attr in self._copy_kwargs}
        cooldown = self.__class__(error=self.error, mapping=self.mapping, **kwargs)
        cooldown = cooldown(rate=self.rate, per=self.per, type=self.type)
        return cooldown

    def __call__(self, rate:float, per:int, type:commands.BucketType) -> None:
        """Runs the original init method

        Params:
            rate : int
                How many times the command can be called (rate) in a given amount of time (per) before being applied
            per : float
                How many times the command can be called (rate) in a given amount of time (per) before being applied
            type : discord.ext.commands.BucketType
                How the cooldown should be applied
        """

        try:
            if self.type:
                type = self.type
        except AttributeError:
            pass
        super().__init__(rate, per, type)
        return self


def cooldown(rate, per, type=commands.BucketType.default, *, cls:commands.Cooldown=None):
    """A decorator that adds a cooldown to a :class:`.Command`
    or its subclasses.

    A cooldown allows a command to only be used a specific amount
    of times in a specific time frame. These cooldowns can be based
    either on a per-guild, per-channel, per-user, or global basis.
    Denoted by the third argument of ``type`` which must be of enum
    type ``BucketType`` which could be either:

    - ``BucketType.default`` for a global basis.
    - ``BucketType.user`` for a per-user basis.
    - ``BucketType.guild`` for a per-guild basis.
    - ``BucketType.channel`` for a per-channel basis.
    - ``BucketType.member`` for a per-member basis.
    - ``BucketType.category`` for a per-category basis.

    If a cooldown is triggered, then :exc:`.CommandOnCooldown` is triggered in
    :func:`.on_command_error` and the local error handler.

    A command can only have a single cooldown.

    Parameters
    ------------
    rate: :class:`int`
        The number of times a command can be used before triggering a cooldown.
    per: :class:`float`
        The amount of seconds to wait for a cooldown when it's been triggered.
    type: ``BucketType``
        The type of cooldown to have.
    """

    if cls is None:
        cls = Cooldown()

    def decorator(func):
        if isinstance(func, commands.Command):
            mapping = cls.mapping or cls.default_mapping_class()
            func._buckets = mapping(cls(rate, per, type))
        else:
            func.__commands_cooldown__ = cls(rate, per, type)
        return func
    return decorator
