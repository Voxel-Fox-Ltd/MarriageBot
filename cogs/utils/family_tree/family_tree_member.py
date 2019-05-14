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


    def span(self, people_list:list=None, add_parent:bool=False, expand_upwards:bool=False, guild:Guild=None) -> list:
        '''
        Gets a list of every user related to this one
        If "add_parent" and "expand_upwards" are True, then it should add every user in a given tree,
        even if they're related through marriage's parents etc

        Params:
            people_list: list 
                The list of users who are currently in the tree (so as to avoid recursion)
            add_parent: bool = False
                Whether or not to add the parent of this user to the people list
            expand_upwards: bool = False
                Whether or not to expand upwards in the tree
            guild: Guild = None
                If added, span will return users only if they're in the given guild

        Returns:
            A list of all people on the family for this user, in no particular order
        '''

        # Don't add yourself again
        if people_list == None:
            people_list = []
        if self in people_list:
            return people_list

        # Filter out non-guild members
        if guild:
            if not guild.get_member(self.id):
                return people_list

        people_list.append(self)

        # Add your parent
        if expand_upwards and add_parent and self._parent:
            parent = self.parent
            people_list = parent.span(people_list, add_parent=True, expand_upwards=expand_upwards, guild=guild)

        # Add your children
        if self._children:
            children = self.children
            for child in children:
                people_list = child.span(people_list, add_parent=False, expand_upwards=expand_upwards, guild=guild)

        # Add your partner
        if self._partner:
            partner = self.partner
            people_list = partner.span(people_list, add_parent=True, expand_upwards=expand_upwards, guild=guild)

        # Remove dupes, should they be in there
        return people_list


    def get_root(self, guild:Guild=None):
        '''
        Expands backwards into the tree up to a root user
        Only goes up one line of family so it cannot add your spouse's parents etc

        Params: 
            guild: Guild = None
                If you want to get users only from a given guild, supply a guild here
        '''

        # Set a default user to look at
        root_user = self

        # Avoid loops
        already_processed = []

        while True:
            # Loop avoidance 2.0
            if root_user in already_processed:
                return root_user
            already_processed.append(root_user)

            if guild:
                # See if they have a parent
                if root_user._parent and guild.get_member(root_user._parent):
                    root_user = root_user.parent

                # They don't but their partner might
                elif root_user._partner and guild.get_member(root_user._partner):
                    partner = root_user.partner
                    if partner._parent and guild.get_member(partner._parent):
                        root_user = partner.parent
                else:
                    return root_user
            else:
                if root_user._parent:
                    root_user = root_user.parent
                elif root_user._partner:
                    partner = root_user.partner 
                    if partner._parent:
                        root_user = partner.parent
                else:
                    return root_user


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
        if target_user.id == self.id:
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


    def generate_gedcom_script(self, bot) -> str:
        '''
        Gives you the INDI and FAM gedcom strings for this family tree
        Includes their spouse, if they have one, and any children
        Small bit of redundancy: a family will be added twice if they have a spouse. 
        '''

        '''
        Example family:
        0 @I1@ INDI
            1 NAME John /Smith/
            1 FAMS @F1@
        0 @F1@ FAM
            1 HUSB @I1@
            1 WIFE @I2@
            1 CHIL @I3@
        '''

        gedcom_text = []
        family_id_cache = {}  # id: family count
        full_family = self.span(add_parent=True, expand_upwards=True)

        for i in full_family:
            name = self.bot.get_name(i.id)
            working_text = [
                f'0 @I{i.tree_id}@ INDI',
                f'\t1 NAME {name}'
            ]

            # If you have a parent, get added to their family
            if i._parent:
                parent = i.parent
                if parent.id in family_id_cache:
                    working_text.append(f'\t1 FAMC @F{family_id_cache[parent.id]}@')
                elif parent._partner and parent._partner in family_id_cache:
                    working_text.append(f'\t1 FAMC @F{family_id_cache[parent._partner]}@')
                else:
                    working_text.append(f'\t1 FAMC @F{parent.tree_id}@')

            # If you have children or a partner, generate a family
            if i._children or i._partner:
                children = i.children 
                partner = i.partner

                # See if you need to make a new family or be added to one already made
                try:
                    insert_location = gedcom_text.index(f'\t1 HUSB @I{i.tree_id}@')
                    # Above will throw error if this user is not in a tree already

                    working_text.append(f'\t1 FAMS @F{family_id_cache[partner.id]}@')
                    family_id_cache[i.id] = partner.tree_id
                    for c in children:
                        gedcom_text.insert(insert_location, f'\t1 CHIL @I{c.tree_id}@')
                except ValueError:
                    family_id_cache[i.id] = i.tree_id
                    working_text.append(f'\t1 FAMS @F{i.tree_id}@')
                    working_text.append(f'0 @F{i.tree_id}@ FAM')
                    working_text.append(f'\t1 WIFE @I{i.tree_id}@')
                    if i.partner:
                        working_text.append(f'\t1 HUSB @I{partner.tree_id}@')
                    for c in children:
                        working_text.append(f'\t1 CHIL @I{c.tree_id}@')

            gedcom_text.extend(working_text)
        x = '0 HEAD\n\t1 GEDC\n\t\t2 VERS 5.5\n\t\t2 FORM LINEAGE-LINKED\n\t1 CHAR UNICODE\n' + '\n'.join(gedcom_text) + '\n0 TRLR'
        return x


    def generational_span(self, people_dict:dict=None, depth:int=0, add_parent:bool=False, expand_upwards:bool=False, guild:Guild=None, all_people:list=None, recursive_depth:int=0) -> dict:
        '''
        Gets a list of every user related to this one
        If "add_parent" and "expand_upwards" are True, then it should add every user in a given tree,
        even if they're related through marriage's parents etc

        Params:
            people_dict: dict 
                The dict of users who are currently in the tree (so as to avoid recursion)
            depth: int = 0
                The current generation of the tree span
            add_parent: bool = False
                Whether or not to add the parent of this user to the people list
            expand_upwards: bool = False
                Whether or not to expand upwards in the tree
            guild: Guild = None
                If added, span will return users only if they're in the given guild
            recursive_depth: int = 0
                How far into the recursion you have gone - this is so we don't get recursion errors

        Returns:
            A list of all people on the family for this user, in no particular order
        '''

        # Don't add yourself again
        if people_dict == None:
            people_dict = {}
        if all_people == None:
            all_people = []
        if self.id in all_people:
            return people_dict
        if recursive_depth >= 500:
            return people_dict
        all_people.append(self.id)

        # Filter out non-guild members
        if guild:
            if not guild.get_member(self.id):
                return people_dict

        # Add to dict
        x = people_dict.get(depth, list())
        x.append(self)
        people_dict[depth] = x

        # Add your children
        if self._children:
            children = self.children
            for child in children:
                people_dict = child.generational_span(people_dict, depth=depth+1, add_parent=False, expand_upwards=expand_upwards, guild=guild, all_people=all_people, recursive_depth=recursive_depth+1)

        # Add your partner
        if self._partner:
            partner = self.partner
            people_dict = partner.generational_span(people_dict, depth=depth, add_parent=True, expand_upwards=expand_upwards, guild=guild, all_people=all_people, recursive_depth=recursive_depth+1)

        # Add your parent
        if expand_upwards and add_parent and self._parent:
            parent = self.parent
            people_dict = parent.generational_span(people_dict, depth=depth-1, add_parent=True, expand_upwards=expand_upwards, guild=guild, all_people=all_people, recursive_depth=recursive_depth+1)

        # Remove dupes, should they be in there
        return people_dict


    async def to_dot_script(self, bot, guild:Guild=None, customised_tree_user:CustomisedTreeUser=None) -> str:
        '''
        Gives you a string of the current family tree that will go through Family

        Params:
            bot: Bot
                Used solely to get the names of people
            guild: Guild = None
                If set to none, does nothing of interest. If set to a guild, will only add
                members to the tree that are in the given guild
        '''

        # Get the generation spanning tree
        root_user = self.get_root(guild=guild)
        if customised_tree_user == None:
            customised_tree_user = CustomisedTreeUser.get(self.id)
        gen_span = root_user.generational_span(guild=guild)
        return await self.to_dot_script_from_generational_span(bot, gen_span, customised_tree_user)

    
    async def to_full_dot_script(self, bot, customised_tree_user:CustomisedTreeUser=None) -> str:
        '''
        Gives you the string of the FULL current family
        '''

        # Get the generation spanning tree
        root_user = self.get_root()
        if customised_tree_user == None:
            customised_tree_user = CustomisedTreeUser.get(self.id)
        gen_span = root_user.generational_span(expand_upwards=True, add_parent=True)
        return await self.to_dot_script_from_generational_span(bot, gen_span, customised_tree_user)


    async def to_dot_script_from_generational_span(self, bot, gen_span:dict, customised_tree_user:CustomisedTreeUser) -> str:
        '''
        Generates the DOT script from a given generational span
        '''

        ctu = customised_tree_user

        # Find my own depth
        my_depth = None
        for depth, l in gen_span.items():
            if self in l:
                my_depth = depth
                break

        # Add my partner and parent 
        if self._partner:
            partner = self.partner
            if partner not in gen_span.get(my_depth, list()):
                x = gen_span.get(my_depth, list())
                x.append(partner)
                gen_span[my_depth] = x
        if self._parent:
            parent = self.parent 
            if parent not in gen_span.get(my_depth-1, list()):
                x = gen_span.get(my_depth-1, list())
                x.append(parent)
                gen_span[my_depth-1] = x

        # Add the labels for each user
        all_text = [
            'digraph {',
            f"\tnode [shape=box, fontcolor={ctu.hex['font']}, color={ctu.hex['edge']}, fillcolor={ctu.hex['node']}, style=filled];",
            f"\tedge [dir=none, color={ctu.hex['edge']}];",
            f"\tbgcolor={ctu.hex['background']}",
            '',
        ]
        all_users = []
        user_parent_tree = {}  # Parent: random_string (the dot between a couple)
        for generation in gen_span.values():
            for i in generation:
                all_users.append(i)
                raw_name = await self.bot.get_name(i.id)
                name = self.NAME_SUBSTITUTION.sub('_', raw_name)
                if i == self:
                    all_text.append(f'\t{i.id}[label="{name}", fillcolor={ctu.hex["highlighted_node"]}, fontcolor={ctu.hex["highlighted_font"]}];')
                else:
                    all_text.append(f'\t{i.id}[label="{name}"];')
        
        # Order the generations
        generation_numbers = sorted(list(gen_span.keys()))

        # Go through each generation's users
        for generation_number in generation_numbers:
            generation = gen_span.get(generation_number)

            # Add each user and their spouse
            added_already = []
            all_text.append("\t{ rank=same;")
            previous_person = None
            for person in generation:
                if person in added_already:
                    continue
                user_parent_tree[person.id] = person.id
                added_already.append(person)
                if previous_person:
                    all_text.append(f"\t\t{previous_person.id} -> {person.id} [style=invis];")
                partner = person.partner
                if partner and partner in generation:
                    user_parent_tree[partner.id] = user_parent_tree[person.id] = get_random_string()
                    all_text.append(f"\t\t{person.id} -> {user_parent_tree[person.id]} -> {partner.id};")
                    all_text.append(f"\t\t{user_parent_tree[person.id]} {self.INVISIBLE}")
                    added_already.append(partner)
                    previous_person = partner
                else:
                    all_text.append(f"\t\t{person.id};")
                    previous_person = person
            all_text.append("\t}")

            # Add the connecting node from parent to child
            all_text.append("\t{")
            for person in generation:
                if person._children:
                    children = person.children
                    if any([i in all_users for i in children]):
                        all_text.append(f"\t\th{user_parent_tree[person.id]} {self.INVISIBLE};")
            all_text.append("\t}")

            # Add the lines from parent to node to child
            added_already.clear()
            for person in generation:
                if person._children:
                    children = person.children
                    if any([i in all_users for i in children]):
                        if user_parent_tree[person.id] in added_already:
                            pass
                        else:
                            all_text.append(f"\t\t{user_parent_tree[person.id]} -> h{user_parent_tree[person.id]};")
                            added_already.append(user_parent_tree[person.id])
                        for child in [i for i in children if i in all_users]:
                            all_text.append(f"\t\th{user_parent_tree[person.id]} -> {child.id};")
        all_text.append("}")

        return '\n'.join(all_text)
