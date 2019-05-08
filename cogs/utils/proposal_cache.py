from typing import Union

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

    async def add(self, instigator:Union[User, int], target:Union[User, int], cog:str):
        async with self.bot.redis() as re:
            await re.publish_json('ProposalCacheAdd', {
                'instigator': get_id(instigator),
                'target': get_id(target),
                'cog': cog
            })
        self.raw_add(instigator, target, cog)


    def raw_add(self, instigator:Union[User, int], target:Union[User, int], cog:str):
        '''Adds a user to the proposal cache'''

        # Add to cache
        self[get_id(instigator)] = ('INSTIGATOR', cog)
        self[get_id(target)] = ('TARGET', cog)
    
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
