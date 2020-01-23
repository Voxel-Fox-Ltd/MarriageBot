import typing

import discord
from discord.ext import commands


class Cooldown(commands.Cooldown):
    """A class handling the cooldown for an individual user

    Params:
        rate : int
            How many times the command can be called (rate) in a given amount of time (per) before being applied
        per : float
            How many times the command can be called (rate) in a given amount of time (per) before being applied
        type : discord.ext.commands.BucketType
            How the cooldown should be applied

    Attrs:
        _window : float
            The start time (time.time(), Unix timestamp) for the cooldown
        _tokens : int
            How many more times the given command can be called in the timeframe
        _last : float
            The time (time.time(), Unix timestamp) that the command was last sucessfully called at
    """

    __slots__ = ('rate', 'per', 'type', '_window', '_tokens', '_last')


    def __init__(self, rate:int, per:float, type:commands.BucketType):
        super().__init__(rate, per, type)

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

    def update_rate_limit(self, current:float=None) -> None:
        """Updates the rate limit for the command, as it has now been called

        Params:
            current : float = None
                The current time, or now (via time.time())
        """

        return super().update_rate_limit(current)

    def reset(self) -> None:
        """Resets the cooldown for the given command"""

        return super().reset()

    def copy(self) -> commands.Cooldown:
        """Returns a copy of the cooldown"""

        return self.__class__(self.rate, self.per, self.type)


class CooldownMapping(commands.CooldownMapping):
    """A mapping of cooldowns and who's run them, so we can keep track of individuals' rate limits

    Params:
        original : commands.Cooldown
            The original cooldown that this mapping refers to

    Attrs:
        _cache : typing.Dict[int, commands.Cooldown]
            The cache for the individual and the applied cooldown
    """

    def __init__(self, original:commands.Cooldown):
        super().__init__(original)

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


def cooldown(rate, per, type=commands.BucketType.default, *, mapping=commands.CooldownMapping, cls=commands.Cooldown):
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
    
    def decorator(func):
        if isinstance(func, Command):
            func._buckets = mapping(cls(rate, per, type))
        else:
            func.__commands_cooldown__ = cls(rate, per, type)
        return func
    return decorator
