from random import choices
from asyncio import create_subprocess_exec, get_event_loop
from logging import getLogger

from discord import Member
from asyncpg import connect as _connect, Connection, create_pool as _create_pool
from asyncpg.pool import Pool


logger = getLogger('marriagebot.db')



class DatabaseConnection(object):

    config = None
    pool = None


    def __init__(self, connection:Connection=None):
        self.conn = connection


    @classmethod
    async def create_pool(cls, config:dict):
        cls.config = config
        cls.pool = await _create_pool(**config)


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
        logger.debug(f"Running SQL: {sql} ({args!s})")
        x = await self.conn.fetch(sql, *args)

        # If it got something, return the dict, else None
        if x:
            return x
        if 'select' in sql.casefold() or 'returning' in sql.casefold():
            return []
        return None


    async def destroy(self, user_id:int):
        '''
        Removes a given user ID form all parts of the database
        '''

        await self('DELETE FROM marriages WHERE user_id=$1 OR partner_id=$1', user_id)
        await self('DELETE FROM parents WHERE child_id=$1 OR parent_id=$1', user_id)


    async def marry(self, instigator:Member, target:Member, guild_id:int, marriage_id:str=None):
        '''
        Marries two users together
        Remains in the Database class solely as you need the "idnumber" field.
        '''

        if marriage_id == None:
            id_number = 'a'
        else:
            id_number = marriage_id
        # marriage_id, user_id, user_name, partner_id, partner_name, valid
        await self(
            'INSERT INTO marriages (user_id, partner_id, guild_id) VALUES ($1, $2, $3)',
            instigator.id,
            target.id,
            guild_id,
        )
        if marriage_id == None:
            await self.marry(target, instigator, guild_id, id_number)  # Run it again with instigator/target flipped
