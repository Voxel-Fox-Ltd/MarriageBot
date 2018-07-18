from random import choice
from discord import Member
from asyncpg import connect


RANDOM_CHARACTERS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890-_'


class DatabaseConnection(object):

    config = None

    def __init__(self):
        self.db = None

    async def __aenter__(self):
        self.db = await connect(**self.config)
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

    async def make_id(self, table:str, id_field:str) -> str:
        '''
        Makes a random ID that hasn't appeared in the database before for a given table
        '''

        while True:
            idnumber = ''
            for i in range(11):
                idnumber += choice(RANDOM_CHARACTERS)
            x = await self(f'SELECT * FROM {table} WHERE {id_field}=$1', idnumber)
            if not x:
                return idnumber

    async def get_marriage(self, user:Member):
        '''
        Gets a marriage dictionary from the database for the given user
        '''

        x = await self('SELECT * FROM marriages WHERE user_id=$1 AND valid=TRUE', user.id)
        if x:
            y = await self('SELECT * FROM marriages WHERE marriage_id=$1 AND valid=TRUE', x[0]['marriage_id'])
            return [x[0], y[0]]
        return None

    async def add_event(self, instigator:Member, target:Member, event:str):
        '''
        Adds an event to the events table
        '''

        idnumber = await self.make_id('events', 'event_id')
        # event_id, event_type, instigator, target, time
        await self(
            'INSERT INTO events VALUES ($1, $2, $3, $4, NOW())', 
            idnumber,
            event,
            instigator.id,
            target.id 
        )

    async def marry(self, instigator:Member, target:Member, marriage_id:str=None):
        '''
        Marries two users together
        '''

        if marriage_id == None:
            idnumber = await self.make_id('marriages', 'marriage_id')
        else:
            idnumber = marriage_id
        # marriage_id, user_id, user_name, partner_id, partner_name, valid
        await self(
            'INSERT INTO marriages VALUES ($1, $2, $3, TRUE)',
            idnumber,
            instigator.id,
            target.id,
        )
        await self.add_event(instigator, target, 'MARRIAGE')
        if marriage_id == None:
            await self.marry(target, instigator, idnumber)  # Run it again with instigator/target flipped

    async def divorce(self, instigator:Member, target:Member, marriage_id:str):
        '''
        Divorces two married people
        '''

        instigator
        await self.add_event(instigator=instigator, target=target, event='DIVORCE')
        await self.add_event(instigator=target, target=instigator, event='DIVORCE')
        await self('UPDATE marriages SET valid=FALSE WHERE marriage_id=$1', marriage_id)

    async def get_parent(self, user:Member):
        '''
        Finds the parentage info of a given user
        '''

        x = await self('SELECT * FROM parents WHERE child_id=$1', user.id)
        if x:
            return x[0]
        return None
