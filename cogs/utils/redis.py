from logging import getLogger

from aioredis import create_pool as _create_pool, RedisConnection


logger = getLogger('marriagebot.redis')



class RedisConnection(object):

    config = None
    pool = None


    def __init__(self, connection:RedisConnection=None, sustain:bool=False):
        self.conn = connection
        self.sustain = sustain


    @classmethod
    async def create_pool(cls, config:dict):
        cls.config = config
        address = config.pop('host'), config.pop('port')
        cls.pool = await _create_pool(address, **config)


    async def __aenter__(self):
        if not self.conn:
            self.conn = await self.pool.acquire()
        return self


    async def __aexit__(self, exc_type, exc, tb):
        if not self.sustain:
            self.pool.release(self.conn)
            self.conn = None
            del self


    async def set(self, key, value):
        return await self.conn.execute('set', key, value)


    async def get(self, key):
        return await self.conn.execute('get', key)
