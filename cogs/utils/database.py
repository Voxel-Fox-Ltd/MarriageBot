from asyncpg import connect

class DatabaseConnection(object):

    config = None

    def __init__(self):
        self.db = None

    async def __aenter__(self):
        self.db = await connect(self.config)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.db.close()
        self.db = None

    async def __call__(self, sql:str, *args):
        '''
        Runs a line of SQL using the internal database
        '''

        # Runs the SQL
        x = await self.db.fetch(sql, *args)

        # If it got something, return the dict, else None
        if x:
            return x
        return None
