from typing import Union
from datetime import datetime as dt, timedelta

from discord import User


def get_id(user:Union[User, int]):
    try:
        return user.id 
    except AttributeError:
        return user


class ProposalCache(dict):


    bot = None


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self[user_id] = (ROLE, COG, TIMEOUT)


    def get(self, key, d=None, ignore_timeout:bool=False, *args, **kwargs):
        '''Only return if not timed out'''

        item = super().get(key, d, *args, **kwargs)
        if item in [None, d]:
            return item
        if len(item) == 2:
            return item 
        if dt.now() > item[2] and ignore_timeout is False:
            return d
        return item


    async def add(self, instigator:Union[User, int], target:Union[User, int], cog:str):
        timeout_time = dt.now() + timedelta(seconds=60)
        async with self.bot.redis() as re:
            await re.publish_json('ProposalCacheAdd', {
                'instigator': get_id(instigator),
                'target': get_id(target),
                'cog': cog,
                'timeout_time': timeout_time.isoformat()
            })
        self.raw_add(instigator, target, cog, timeout_time)


    def raw_add(self, instigator:Union[User, int], target:Union[User, int], cog:str, timeout_time:dt):
        '''Adds a user to the proposal cache'''

        # Add to cache
        if isinstance(timeout_time, str):
            timeout_time = dt.strptime(timeout_time, "%Y-%m-%dT%H:%M:%S.%f")
        self[get_id(instigator)] = ('INSTIGATOR', cog, timeout_time)
        self[get_id(target)] = ('TARGET', cog, timeout_time)
    

    async def remove(self, *elements):
        async with self.bot.redis() as re:
            await re.publish_json('ProposalCacheRemove', [get_id(i) for i in elements])
        self.raw_remove(*elements)


    def raw_remove(self, *elements):
        x = []
        for i in elements:
            i = get_id(i)
            try:
                x.append(self.pop(i))
            except KeyError:
                pass
        return x        
