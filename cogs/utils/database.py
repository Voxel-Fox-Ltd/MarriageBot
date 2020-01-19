import typing
import logging
from datetime import datetime as dt

import discord
import asyncpg


class DatabaseConnection(object):
    """A helper class to wrap around an asyncpg.Connection object so as
    to make it a little easier to use"""

    config: dict = None
    pool: asyncpg.pool.Pool = None
    logger: logging.Logger = None
    __slots__ = ('conn', 'transaction')

    def __init__(self, connection:asyncpg.Connection=None, transaction:asyncpg.transaction.Transaction=None):
        self.conn = connection
        self.transaction = transaction

    @staticmethod
    async def create_pool(config:dict) -> None:
        """Creates the database pool and plonks it in DatabaseConnection.pool"""

        DatabaseConnection.config = config
        DatabaseConnection.pool = await asyncpg.create_pool(**config)

    @classmethod
    async def get_connection(cls) -> 'DatabaseConnection':
        """Acquires a connection to the database from the pool"""

        conn = await cls.pool.acquire()
        return cls(conn)

    async def disconnect(self) -> None:
        """Releases a connection from the pool back to the mix"""

        await self.pool.release(self.conn)
        self.conn = None
        del self

    async def start_transaction(self):
        """Creates a database object for a transaction"""

        self.transaction = self.conn.transaction()
        await self.transaction.start()

    async def commit_transaction(self):
        """Commits the transaction wew lad"""

        await self.transaction.commit()
        self.transaction = None

    async def __aenter__(self):
        self.conn = await self.pool.acquire()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.pool.release(self.conn)
        self.conn = None
        del self

    async def __call__(self, sql:str, *args) -> typing.Union[typing.List[dict], None]:
        """Runs a line of SQL and returns a list, if things are expected back,
        or None, if nothing of interest is happening"""

        # Runs the SQL
        self.logger.debug(f"Running SQL: {sql} {args!s}")
        if 'select' in sql.casefold() or 'returning' in sql.casefold():
            x = await self.conn.fetch(sql, *args)
        else:
            await self.conn.execute(sql, *args)
            return

        # If it got something, return the dict, else None
        if x:
            return x
        if 'select' in sql.casefold() or 'returning' in sql.casefold():
            return []
        return None

    async def marry(self, instigator:typing.Union[int, discord.User], target:typing.Union[int, discord.User], guild_id:int):
        """Marries two given Discord users together"""

        instigator_id = getattr(instigator, 'id', instigator)
        target_id = getattr(target, 'id', target)

        await self.start_transaction()
        timestamp = dt.utcnow()
        try:
            await self(
                'INSERT INTO marriages (user_id, partner_id, guild_id, timestamp) VALUES ($1, $2, $3, $4)',
                instigator_id, target_id, guild_id, timestamp,
            )
            await self(
                'INSERT INTO marriages (user_id, partner_id, guild_id, timestamp) VALUES ($2, $1, $3, $4)',
                instigator_id, target_id, guild_id, timestamp,
            )
        except Exception as e:
            await self.transaction.rollback()
            raise e
        await self.commit_transaction()
