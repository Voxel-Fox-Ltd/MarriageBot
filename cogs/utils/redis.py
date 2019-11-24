import logging

import aioredis


class RedisConnection(object):
    """A wrapper for an aioredis.Redis object, to make things easier to work
    with for me"""

    config: dict = None
    pool: aioredis.Redis = None
    logger: logging.Logger = None  # Set as a child of bot.logger

    def __init__(self, connection:aioredis.RedisConnection=None):
        self.conn = connection

    @staticmethod
    async def create_pool(config:dict):
        """Creates and connects the pool object"""

        RedisConnection.config = config.copy()
        address = config.pop('host'), config.pop('port')
        RedisConnection.pool = await aioredis.create_redis_pool(address, **config)

    async def __aenter__(self) -> 'cogs.utils.redis.RedisConnection':
        self.conn = self.pool
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    @classmethod
    async def get_connection(cls) -> 'cogs.utils.redis.RedisConnection':
        """Acquires a connection from the connection pool"""

        conn = cls.pool
        return cls(conn)

    async def disconnect(self) -> None:
        """Releases a connection back into the connection pool"""

        del self

    async def publish_json(self, channel:str, json:dict) -> None:
        """Publishes some JSON to a given redis channel"""

        self.logger.debug(f"Publishing JSON to channel {channel}: {json!s}")
        return await self.conn.publish_json(channel, json)

    async def publish(self, channel:str, message:str) -> None:
        """Publishes a message to a given redis channel"""

        self.logger.debug(f"Publishing message to channel {channel}: {message}")
        return await self.conn.publish(channel, message)

    async def set(self, key:str, value:str) -> None:
        """Sets a key/value pair in the redis DB"""

        self.logger.debug(f"Publishing Redis key:value pair with {key}:{value}")
        return await self.conn.set(key, value)

    async def get(self, key:str) -> str:
        """Grabs a value from the redis DB given a key"""

        v = await self.conn.get(key)
        self.logger.debug(f"Getting Redis key with {key}:{v!s}")
        if v:
            return v.decode()
        return v
