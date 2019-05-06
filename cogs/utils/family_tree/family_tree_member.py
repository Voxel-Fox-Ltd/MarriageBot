from re import compile
from random import choices
from string import ascii_letters

from discord import User, Guild
# from unidecode import unidecode

from cogs.utils.customised_tree_user import CustomisedTreeUser
from cogs.utils.family_tree.relation_simplifier import Simplifier


def get_random_string(length:int=10):
    return ''.join(choices(ascii_letters, k=length))


class FamilyTreeMember(object):
    '''
    A family member to go in the tree

    Params:
        discord_id: int 
        children: list[int]
        parent_id: int
        partner_id: int
        guild_id: int=None
    '''

    all_users = {}  # id: FamilyTreeMember
    NAME_SUBSTITUTION = compile(r'[^\x00-\x7F\x80-\xFF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF]|\"|\(|\)')
    INVISIBLE = '[shape=circle, label="", height=0.001, width=0.001]'  # For the DOT script
    bot = None


    def __init__(self, discord_id:int, children:list=None, parent_id:int=None, partner_id:int=None, guild_id:int=0):
        self.id = discord_id  # The ID of the user whose tree this is
        self._children = children or list()  # List of the children's IDs
        self._parent = parent_id  # ID of the parent
        self._partner = partner_id  # ID of the partner
        self.tree_id = get_random_string()  # Used purely for the dot joining two spouses in the GZ script
        self._guild_id = guild_id  # The guild that this FTM is from
        self.all_users[(self.id, self._guild_id)] = self  # Add this object to cache


    @classmethod 
    def get(cls, discord_id:int, guild_id:int=0):
        '''Gives you the object for a given user'''

        v = cls.all_users.get((discord_id, guild_id))
        if v:
            return v 
        return cls(discord_id=discord_id, guild_id=guild_id)


    def to_json(self) -> dict:
        '''Converts the object to JSON format so you can throw it through redis'''

        return {
            'discord_id': self.id,
            'children': self._children,
            'parent_id': self._parent,
            'partner_id': self._partner,
            'guild_id': self._guild_id,
        }


    @classmethod 
    def from_json(cls, data:dict):
        '''Loads an object from JSON to the cache'''

        # Yeah this is completely pointless
        return cls(**data)

    
    def __repr__(self) -> str:
        '''Print print print wew'''

        return f"FamilyTreeMember[{self.id} <{len(self._children)} children>]"

    
    def __eq__(self, other) -> bool:
        '''Says if this instance shares the same ID as another instance''' 

        if not isinstance(other, self.__class__):
            return False
        return all([
            __class__ == other.__class__, 
            self.id == other.id,
            self._guild_id == other._guild_id, 
        ])


    @property
    def partner(self):
        '''Gets you the instance of this user's partner'''

        if self._partner:
            return self.get(self._partner, self._guild_id)
        return None


    @property
    def parent(self):
        '''Gets you the instance of this user's parent'''

        if self._parent:
            return self.get(self._parent, self._guild_id)
        return None


    @property
    def children(self) -> list:
        '''Gets you the list of children instances for this user'''

        if self._children:
            return [self.get(i, self._guild_id) for i in self._children]
        return []


    @property
    def is_empty(self) -> bool:
        '''Is this instance useless'''

        return all([
            len(self._children) == 0, 
            self._parent == None,
            self._partner == None,
        ])


    async def fetch_guild(self) -> Guild:
        '''Fetches the guild from the bot via HTTP method'''

        return await self.bot.fetch_guild(self._guild_id)


    def get_relation(self, target_user):
        '''Gets your relation to another given FamilyTreeMember object'''

        text = self.get_unshortened_relation(target_user)
        return Simplifier().simplify(text)


    def get_unshortened_relation(self, target_user, working_relation:list=None, added_already:list=None) -> str:
        '''
        Gets your relation to the other given user or None

        Params:
            target_user : The user who you want to list the relation to
            working_relation[list] : The list of relation steps it's taking to get
            added_already[list] : So we can keep track of who's been looked at before
        '''

        # Set default values
        if working_relation == None:
            working_relation = []
        if added_already == None:
            added_already = []

        # You're doing a loop - return None
        if self.id in added_already:
            return None

        # We hit the jackpot - return the made up string
        if target_user == self.id:
            ret_string = "'s ".join(working_relation)
            return ret_string

        # Add self to list of checked people
        added_already.append(self.id)

        # Check parent
        if self._parent and self._parent not in added_already:
            parent = self.parent
            x = parent.get_unshortened_relation(
                target_user, 
                working_relation=working_relation+['parent'], 
                added_already=added_already
            )
            if x: return x 

        # Check partner
        if self._partner and self._partner not in added_already:
            partner = self.partner
            x = partner.get_unshortened_relation(
                target_user, 
                working_relation=working_relation+['partner'], 
                added_already=added_already
            )
            if x: return x 

        # Check children
        if self._children:
            children = self.children
            for i in [o for o in children if o not in added_already]:
                x = i.get_unshortened_relation(
                    target_user, 
                    working_relation=working_relation+['child'], 
                    added_already=added_already
                )
                if x: return x 
        return None
