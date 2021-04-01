import typing

import voxelbotutils as utils


class DiscordNameManager(object):

    cached_names: typing.Dict[int, 'DiscordNameManager'] = {}

    __slots__ = ("user_id", "name", "age",)

    def __init__(self, user_id:int, name:str=None):
        self.user_id: int = user_id
        self._name: str = name
        self.age: int = 0
        self.cached_names[self.user_id] = self

    @property
    def name(self):
        self.age += 1
        return self._name

    @name.setter
    def name(self, new_name:str):
        self.age = 0
        self._name = new_name

    @property
    def name_is_valid(self):
        return self.age <= 3

    async def fetch_name(self, bot:utils.Bot) -> str:
        """
        Fetch the name of the current user - first trying from Redis, then trying from the
        API (if we couldn't get from Redis the first time then we add it after fetching from
        the API).
        """

        async with bot.redis() as re:
            v = await re.get(f"UserName-{self.user_id}")
        if v:
            self.name = v
            return v
        try:
            user = await bot.fetch_user(self.user_id)
            name = str(user)
        except Exception:
            name = "Deleted User"
        async with bot.redis() as re:
            await re.set(f"UserName-{self.user_id}", name)
        self.name = name
        return name

    @classmethod
    async def fetch_name_by_id(cls, bot:utils.Bot, user_id:int) -> str:
        """
        Get the name for a user given their ID.

        Args:
            bot (utils.Bot): The bot instance that we can use to fetch from the API/Redis with.
            user_id (int): The ID of the user we want to grab the name of.

        Returns:
            str: The user's name.
        """

        # Grab our cached object
        v = cls.cached_names.get(user_id)
        if v is None:
            v = cls(user_id)

        # See if it has a name
        if v.name_is_valid:
            return v.name

        # Grab a new name from the cache for them
        return await v.fetch_name(bot)
