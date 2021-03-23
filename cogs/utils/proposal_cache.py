import typing
from datetime import datetime as dt, timedelta

import discord


class ProposalCacheUser(object):

    __slots__ = ("user_id", "timestamp",)

    def __init__(self, user_id:int, timestamp:dt):
        self.user_id = user_id
        self.timestamp = timestamp

    @classmethod
    def from_json(cls, data:dict):
        return cls(
            data.pop("user_id"),
            dt.fromtimestamp(data.pop("timestamp")),
        )

    def to_json(self):
        return {
            "user_id": self.user_id,
            "timestamp": self.timestamp.timestmap(),
        }


class ProposalCache(dict):
    """
    A helper class to wrap around a dictionary so I can easily
    work out how to deal with what I'm given here instead of repeatedly
    in every cog.
    """

    bot = None

    def get(self, key, *args, **kwargs):
        """
        Gets a key from self, as a normal dict would - but here we check
        if the timeout time has passed.
        """

        cached_user: ProposalCacheUser = super().get(key, *args, **kwargs)
        if cached_user is None:
            return cached_user
        if dt.now() > cached_user.timestamp:
            return None
        return cached_user

    async def redis_add(self, user:discord.User, expiry_seconds:int=60):
        """
        Add a user to the cache (as a rudimentary lock) with a given expiry time.

        Args:
            user (discord.User): The user who we want to add.
            expiry_seconds (int, optional): How long the expiry time on the cache should be.
        """

        timeout_time = dt.now() + timedelta(seconds=expiry_seconds)
        async with self.bot.redis() as re:
            await re.publish('ProposalCacheAdd', {
                'user': user.id,
                'timeout_time': timeout_time.timestamp()
            })
        self.raw_add(user, timeout_time)

    def raw_add(self, user:discord.User, timeout_time:typing.Union[dt, float]):
        """
        Adds a user to the cache without pinging the redis channel.

        Args:
            user (discord.User): The user who we want to add.
            timeout_time (typing.Union[dt, float]): The time (as a datetime object or a timestamp) when this
                cached item should expire.
        """

        # Add to cache
        if isinstance(timeout_time, str):
            timeout_time = dt.fromtimestamp(timeout_time)  # Parse the time from string to DT
        self[user.id] = ProposalCacheUser(user.id, timeout_time)

    async def redis_remove(self, *users:discord.User):
        """
        Removes the given users via redis.

        Args:
            *users (discord.User): The users who we want to remove.
        """

        async with self.bot.redis() as re:
            await re.publish('ProposalCacheRemove', users)

    def raw_remove(self, *users:discord.User) -> list:
        """
        Pops some users from the cache

        Args:
            *users (discord.User): The users who we want to remove.
        """

        for i in users:
            try:
                self.pop(i.id)
            except KeyError:
                pass
