import discord


class ShallowUser(object):
    """A user object that's meant to represent simply a user's NAME (via their ID),
    and how soon a given user should again be pulled from the API or from Redis

    Params:
        user_id: int
            The ID for a given user
        name: str
            The name for the user
        age: int
            How long ago this user's information was pulled from redis
            Starts at 0, should pull again when set to 10
    """

    LIFETIME_THRESHOLD = 10  # How long the class lasts for before re-fetching

    def __init__(self, user_id: int, name: str = None, age: int = None):
        self.user_id = user_id
        self.name = name
        self.age = age if age is not None else self.LIFETIME_THRESHOLD
        self.fetch_when_expired = True

    async def get_name(self, bot) -> str:
        """Gets the name of the given user, first locally, then from redis if expired"""

        if self.age >= self.LIFETIME_THRESHOLD:
            await self.fetch_from_redis(bot)
            return self.name
        self.age += 1
        return self.name

    async def fetch_from_api(self, bot) -> str:
        """Fetches information for the given user from the Discord API"""

        # Grab user data
        try:
            data = await bot.fetch_user(self.user_id)
        except (discord.Forbidden, discord.NotFound):
            self.name = "Deleted User"
            self.age = -1  # This should never change babey
            self.fetch_when_expired = True
        else:
            self.name = str(data)
            self.age = 0
            self.fetch_when_expired = False

        # Push it to redis
        async with bot.redis() as re:
            await re.set(f"UserName-{self.user_id}", self.name)

        # Return data
        return self.name

    async def fetch_from_redis(self, bot) -> str:
        """Fetches information for the given user from the redis cache"""

        async with bot.redis() as re:
            self.name = await re.get(f"UserName-{self.user_id}")
        self.age = 0
        self.fetch_when_expired = True  # We can't trust redis forever
        if self.name is None:
            return await self.fetch_from_api(bot)
        return self.name
