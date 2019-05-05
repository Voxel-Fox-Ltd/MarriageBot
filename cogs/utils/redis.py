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
        if not self.conn:
            self.conn = self.pool
        return self


    async def __aexit__(self, exc_type, exc, tb):
        pass


    async def publish(self, channel:str, value:Union[dict, list]) -> None:
        '''Pushes a JSON value to a channel'''

        return self.conn.publish_json(channel, value)


    async def subscribe(self, channel:str):
        '''Subscribes you to a channel'''
        
        return await self.conn.subscribe(channel)
