import logging
import typing

import aioredis


class RedisConnection(object):
    """A wrapper for an aioredis.Redis object, to make things easier to work
    with for me"""

    config: dict = None
    pool: aioredis.Redis = None
    logger: logging.Logger = None  # Set as a child of bot.logger

    def __init__(self, connection:aioredis.RedisConnection=None):
        self.conn = connection

    @classmethod
    async def create_pool(cls, config:dict) -> None:
        """Creates and connects the pool object"""

        cls.config = config.copy()
        modified_config = config.copy()
        if modified_config.pop('enabled', True) is False:
            raise NotImplementedError("The Redis connection has been disabled.")
        address = modified_config.pop('host'), modified_config.pop('port')
        cls.pool = await aioredis.create_redis_pool(address, **modified_config)

    async def __aenter__(self):
        self.conn = self.pool
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    @classmethod
    async def get_connection(cls):
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

        self.logger.debug(f"Setting Redis key:value pair with {key}:{value}")
        return await self.conn.set(key, value)

    async def get(self, key:str) -> str:
        """Grabs a value from the redis DB given a key"""

        v = await self.conn.get(key)
        self.logger.debug(f"Getting Redis from key with {key}")
        if v:
            return v.decode()
        return v

    async def mget(self, key:str, *keys) -> typing.List[str]:
        """Grabs a value from the redis DB given a key"""

        keys = [key] + keys
        v = await self.conn.mget(key)
        self.logger.debug(f"Getting Redis from keys with {key}")
        if v:
            return [i.decode() for i in v]
        return v
