import discord
from discord.ext import commands

from cogs.utils.custom_bot import CustomBot
from cogs.utils.redis import RedisConnection


class ShallowUser(object):
    """A user object that's meant to represent simply a user's NAME (via their ID),
    and how soon a given user should again be pulled from the API or from Redis

    Params:
        user_id: int
            The ID for a given user
        name: str
            The name for the user
        age: int
            How long ago this user's information was pulled from the API
            Starts at 0, should pull again from the API when set to 10
    """

    LIFETIME_THRESHOLD = 10  # How long the class lasts for before re-fetching

    def __init__(self, user_id:int, name:str=None, age:int=None):
        self.user_id = user_id
        self.name = name
        self.age = age if age is not None else self.LIFETIME_THRESHOLD
        self.fetch_when_expired = True

    async def get_name(self, bot:CustomBot) -> str:
        """Gets the name of the given user, first locally, then from redis, and then the API if expired"""

        if self.age >= self.LIFETIME_THRESHOLD and self.fetch_when_expired:
            await self.fetch_from_api(bot)
            return self.name
        elif self.age >= self.LIFETIME_THRESHOLD:
            async with bot.redis() as re:
                await self.fetch_from_redis(re)
            return self.name
        self.age += 1
        return self.name

    async def fetch_from_api(self, bot:CustomBot) -> str:
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
            await self.publish(re)

        # Return data
        return self.name

    async def fetch_from_redis(self, redis:RedisConnection) -> str:
        """Fetches information for the given user from the redis cache"""

        self.name = await redis.get(f"UserName-{self.user_id}")
        self.age = 0
        self.fetch_when_expired = True  # We can't trust redis forever
        return self.name

    async def publish(self, redis:RedisConnection):
        """Publishes the user's name and their ID to the redis cache"""

        await redis.set(f"UserName-{self.user_id}", self.name)

