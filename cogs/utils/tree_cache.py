from typing import Union

from discord import User


def get_id(user:Union[User, int]):
    try:
        return user.id 
    except AttributeError:
        return user


class TreeCache(list):

    bot = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def add(self, *users):
        # async with self.bot.redis() as re:
        #     await re.publish_json('TreeCacheAdd', [get_id(i) for i in users])
        self.raw_add(*users)

    def raw_add(self, *users):
        '''Adds a user to the proposal cache'''

        # Add to cache
        for i in users:
            self.append(i)
    
    async def remove(self, *users):
        # async with self.bot.redis() as re:
        #     await re.publish_json('TreeCacheRemove', [get_id(i) for i in users])
        self.raw_remove(*users)

    def raw_remove(self, *users):
        x = []
        for i in users:
            i = get_id(i)
            if i in self:
                x.append(i)
            self.remove(i)
        return x        
