import logging
import typing

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

    @classmethod
    async def create_pool(cls, config:dict) -> None:
        """Creates the database pool and plonks it in DatabaseConnection.pool"""

        cls.config = config.copy()
        if config.pop('enabled', True) is False:
            raise NotImplementedError("The database connection has been disabled.")
        cls.pool = await asyncpg.create_pool(**config)

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

    async def copy_records_to_table(self, table_name, *, records, columns=None, timeout=None):
        """Copies a series of records to a given table"""

        return await self.conn.copy_records_to_table(
            table_name=table_name, records=records,
            columns=columns, timeout=timeout
        )
