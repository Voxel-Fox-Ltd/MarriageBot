from logging import getLogger
from typing import Union

from aioredis import create_redis_pool as _create_redis_pool, RedisConnection


logger = getLogger('marriagebot.redis')



class RedisConnection(object):

    config = None
    pool = None


    def __init__(self, connection:RedisConnection=None, sustain:bool=False):
        self.conn = connection
        self.sustain = sustain


    @classmethod
    def set_config(cls, config:dict):
        address = config.pop('host'), config.pop('port')
        cls.config = dict(address=address, **config)


    @classmethod
    async def create_pool(cls, config:dict):
        cls.config = config
        address = config.pop('host'), config.pop('port')
        cls.pool = await _create_redis_pool(address, **config)


    async def __aenter__(self):
        self.conn = self.pool
        return self


    async def __aexit__(self, exc_type, exc, tb):
        pass


    @classmethod 
    async def get_connection(cls) -> 'RedisConnection':
        '''Gets a connection from the connection pool'''

        conn = cls.pool
        return cls(conn)


    async def disconnect(self) -> None:
        '''Releases a connection from the connection pool'''

        del self

    
    async def publish_json(self, channel:str, json:dict):
        logger.debug(f"Publishing JSON to channel {channel}: {json!s}")
        return await self.conn.publish_json(channel, json)

    
    async def publish(self, channel:str, message:str):
        logger.debug(f"Publishing message to channel {channel}: {message}")
        return await self.conn.publish(channel, message)


    async def set(self, key:str, value:str):
        logger.debug(f"Publishing Redis key:value pair with {key}:{value}")
        return await self.conn.set(key, value)

    
    async def get(self, key:str):
        v = await self.conn.get(key)
        logger.debug(f"Getting Redis key with {key}:{v!s}")
        if v:
            return v.decode()
        return v
