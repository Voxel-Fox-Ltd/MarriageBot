import logging

import asyncpg


class DatabaseConnection(object):
    """A wrapper around asyncpg to let me deal with connections better"""

    config: dict = None
    pool: asyncpg.pool.Pool = None
    logger: logging.Logger = None

    def __init__(self, connection:asyncpg.Connection=None):
        self.conn = connection
        if self.logger is None:
            self.logger = logging.getLogger("database")
            self.__class__.logger.warning(f"No logger has been passed "
                                           "through to {self.__class__.__name__}")

    @classmethod
    async def create_pool(cls, config:dict) -> None:
        """Creates a database pool that'll be used to grab every instance"""

        cls.config = config
        cls.pool = await asyncpg.create_pool(**config)

    @classmethod 
    async def get_connection(cls) -> 'DatabaseConnection':
        """Gets a connection from the connection pool"""

        conn = await cls.pool.acquire()
        return cls(conn)

    async def disconnect(self) -> None:
        """Releases a connection from the database pool"""

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
        """Runs a line of SQL (with arguments) with the internal .conn connection"""

        # Runs the SQL
        self.logger.debug(f"Running SQL: {sql} ({args!s})")
        x = await self.conn.fetch(sql, *args)

        # If it got something, return the dict, else None
        if x:
            return x
        if 'select' in sql.casefold() or 'returning' in sql.casefold():
            return []  # Return an empty dict if I was *expecting* something
        return None
