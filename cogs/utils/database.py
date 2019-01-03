from random import choices
from asyncio import create_subprocess_exec, get_event_loop

from discord import Member
from asyncpg import connect as _connect, Connection, create_pool as _create_pool
from asyncpg.pool import Pool


RANDOM_CHARACTERS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890-_'


class DatabasePoolHolder(object):

    def __init__(self, pool:Pool):
        self.pool = pool


    async def acquire(self):
        conn = await self.pool.acquire()
        return DatabaseConnection(conn, self)


    async def __aenter__(self):
        return self 

    
    async def __aexit__(self, exc_type, exc, tb):
        await self.pool.close()


class DatabaseConnection(object):

    config = None


    def __init__(self, connection:Connection=None, parent:DatabasePoolHolder=None):
        self.conn = connection
        self.parent = parent


    @classmethod
    async def create_pool(cls):
        pool = await _create_pool(**cls.config)
        return DatabasePoolHolder(pool)


    async def connect(self):
        self.conn = await _connect(**self.config)


    async def close(self):
        await self.conn.close()


    async def __aenter__(self):
        if not self.conn:
            self.conn = await _connect(**self.config)
        return self


    async def __aexit__(self, exc_type, exc, tb):
        if self.parent:
            await self.parent.release(self.conn)
        else:
            await self.conn.close()
        self.conn = None


    async def __call__(self, sql:str, *args):
        '''
        Runs a line of SQL using the internal database
        '''

        # Runs the SQL
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

        await self('UPDATE marriages SET valid=False WHERE user_id=$1 OR partner_id=$1', user_id)
        await self('DELETE FROM parents WHERE child_id=$1 OR parent_id=$1', user_id)


    async def make_id(self, table:str, id_field:str) -> str:
        '''
        Makes a random ID that hasn't appeared in the database before for a given table
        '''

        while True:
            id_number = ''.join(choices(RANDOM_CHARACTERS, k=11))
            x = await self(f'SELECT * FROM {table} WHERE {id_field}=$1', id_number)
            if not x:
                break
        return id_number


    async def marry(self, instigator:Member, target:Member, marriage_id:str=None):
        '''
        Marries two users together
        Remains in the Database class solely as you need the "idnumber" field.
        '''

        if marriage_id == None:
            id_number = await self.make_id('marriages', 'marriage_id')
        else:
            id_number = marriage_id
        # marriage_id, user_id, user_name, partner_id, partner_name, valid
        await self(
            'INSERT INTO marriages VALUES ($1, $2, $3, TRUE)',
            id_number,
            instigator.id,
            target.id,
        )
        if marriage_id == None:
            await self.marry(target, instigator, id_number)  # Run it again with instigator/target flipped
