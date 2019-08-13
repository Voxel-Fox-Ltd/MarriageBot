from random import choices
from asyncio import create_subprocess_exec, get_event_loop
from logging import getLogger

from discord import Member
from asyncpg import connect as _connect, Connection, create_pool as _create_pool
from asyncpg.pool import Pool



class DatabaseConnection(object):

    config = None
    pool = None
    logger = None


    def __init__(self, connection:Connection=None):
        self.conn = connection


    @classmethod
    async def create_pool(cls, config:dict):
        cls.config = config
        cls.pool = await _create_pool(**config)


    @classmethod 
    async def get_connection(cls) -> 'DatabaseConnection':
        '''Gets a connection from the connection pool'''

        conn = await cls.pool.acquire()
        return cls(conn)


    async def disconnect(self) -> None:
        '''Releases a connection from the database pool'''

        await self.pool.release(self.conn)
        self.conn = None
        del self


    async def __aenter__(self):
        self.conn = await self.pool.acquire()
        return self


    async def __aexit__(self, exc_type, exc, tb):
        await self.pool.release(self.conn)
        self.conn = None
        del self


    async def __call__(self, sql:str, *args):
        '''
        Runs a line of SQL using the internal database
        '''

        # Runs the SQL
        self.logger.debug(f"Running SQL: {sql} ({args!s})")
        x = await self.conn.fetch(sql, *args)

        # If it got something, return the dict, else None
        if x:
            return x
        if 'select' in sql.casefold() or 'returning' in sql.casefold():
            return []
        return None
