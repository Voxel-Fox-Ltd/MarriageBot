from typing import Union

from discord import User


class ProposalCache(dict):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add(self, instigator:Union[User, int], target:Union[User, int], cog:str):
        '''Adds a user to the proposal cache'''

        # Grab IDs
        if isinstance(instigator, User):
            instigator = instigator.id 
        if isinstance(target, User):
            user = user.id 

        # Add to cache
        self[instigator] = ('INSTIGATOR', cog)
        self[target] = ('TARGET', cog)
    
    def remove(self, *elements):
        x = []
        for i in elements:
            if isinstance(i, User):
                i = i.id
            try:
                x.append(self.pop(i))
            except KeyError:
                pass
        return x        
