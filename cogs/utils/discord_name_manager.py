from __future__ import annotations

from typing import Dict, Optional

from discord.ext import vbu


__all__ = (
    'DiscordNameManager',
)


class DiscordNameManager:

    cached_names: Dict[int, DiscordNameManager] = {}

    __slots__ = (
        "user_id",
        "_name",
        "age",
    )

    def __init__(
            self,
            user_id: int,
            name: Optional[str] = None):
        self.user_id: int = user_id
        self._name: Optional[str] = name
        self.age: int = 0 if self._name else 1_000
        self.cached_names[self.user_id] = self

    @classmethod
    def get(cls, id: int) -> DiscordNameManager:
        try:
            return cls.cached_names[id]
        except KeyError:
            return cls(id)

    @property
    def name(self) -> Optional[str]:
        self.age += 1
        return self._name

    @name.setter
    def name(self, new_name: str):
        if new_name is None:
            return None
        self.age = 0
        self._name = new_name

    @property
    def name_is_valid(self):
        return self.age <= 3

    async def fetch_name(self, bot: vbu.Bot) -> str:
        """
        Fetch the name of the current user - first trying from Redis,
        then trying from the API (if we couldn't get from Redis the
        first time then we add it after fetching from the API).
        """

        # Get the name from redis
        async with vbu.Redis() as re:
            v = await re.get(f"UserName-{self.user_id}")

        # If it exists on Redis, update local cache
        if v:
            self.name = v
            return v

        # Fetch the user
        try:
            user = await bot.fetch_user(self.user_id)
            name = str(user)

        # User doesn't exist
        except Exception:
            name = "Deleted User"

        # Store in redis
        async with vbu.Redis() as re:
            await re.set(f"UserName-{self.user_id}", name)

        # Update and return
        self.name = name
        return name

    @classmethod
    async def fetch_name_by_id(
            cls,
            bot: vbu.Bot,
            user_id: int,
            ignore_name_validity: bool = False) -> str:
        """
        Get the name for a user given their ID.

        Parameters
        ----------
        bot : vbu.Bot
            The bot instance that we can use to fetch from the API/Redis with.
        user_id : int
            The ID of the user we want to grab the name of.
        ignore_name_validity : bool, optional
            Whether to ignore the "should we re-fetch the name" check.

        Returns
        -------
        str
            The user's name.
        """

        # Grab our cached object
        v = cls.cached_names.get(user_id)
        if v is None:
            v = cls(user_id)

        # See if it has a name
        if v.name_is_valid or ignore_name_validity:
            name = v.name
            if name:
                if ignore_name_validity:
                    v.age -= 1  # Don't count this towards name validity so we don't deal with the cache
                return name

        # Grab a new name from the cache for them
        return await v.fetch_name(bot)
