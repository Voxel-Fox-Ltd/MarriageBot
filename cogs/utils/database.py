from random import choices
from asyncio import create_subprocess_exec, get_event_loop
from typing import Union, List
import logging

from discord import Member
from asyncpg import connect as _connect, Connection, create_pool as _create_pool
from asyncpg.pool import Pool


class DatabaseConnection(object):

    config = None
    pool = None
    logger: logging.Logger = None


    def __init__(self, connection:Connection=None):
        self.conn = connection


    @classmethod
    async def create_pool(cls, config:dict) -> None:
        '''Connects the class to the system's postgres instance'''

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


    async def __call__(self, sql:str, *args) -> Union[List[dict], None]:
        '''Runs a line of SQL using the internal database'''

        # Runs the SQL
        self.logger.debug(f"Running SQL: {sql} {args!s}")
        x = await self.conn.fetch(sql, *args)

        # If it got something, return the dict, else None
        if x:
            return x
        if 'select' in sql.casefold() or 'returning' in sql.casefold():
            return []
        return None


    async def destroy(self, user_id:int):
        '''Removes a given user ID form all parts of the database'''

        await self('DELETE FROM marriages WHERE user_id=$1 OR partner_id=$1', user_id)
        await self('DELETE FROM parents WHERE child_id=$1 OR parent_id=$1', user_id)


    async def marry(self, instigator:Member, target:Member, guild_id:int):
        '''Marries two users together'''

        instigator_id = getattr(instigator, 'id', instigator)
        target_id = getattr(target, 'id', target)

        await self(
            'INSERT INTO marriages (user_id, partner_id, guild_id) VALUES ($1, $2, $3)',
            instigator_id, target_id, guild_id,
        )
        await self(
            'INSERT INTO marriages (user_id, partner_id, guild_id) VALUES ($2, $1, $3)',
            instigator_id, target_id, guild_id,
        )
