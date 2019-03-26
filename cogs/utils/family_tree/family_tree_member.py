from re import compile
from random import choice, choices
from string import ascii_letters

from discord import User, File, Guild
from discord.ext.commands import CommandError
from unidecode import unidecode

from cogs.utils.customised_tree_user import CustomisedTreeUser


class TreeRecursionError(CommandError): 
    pass


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
    '''

    all_users = {None: None}  # id: FamilyTreeMember
    NAME_SUBSTITUTION = compile(r'[^\x00-\x7F\x80-\xFF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF]|\"|\(|\)')
    INVISIBLE = '[shape=circle, label="", height=0.001, width=0.001]'  # For the DOT script

    operations = [
        lambda x: x.replace("parent's partner", "parent"),
        lambda x: x.replace("partner's child", "child"),
        lambda x: x.replace("parent's sibling", "aunt/uncle"),
        lambda x: x.replace("aunt/uncle's child", "cousin"),
        lambda x: x.replace("parent's child", "sibling"),
        lambda x: x.replace("sibling's child", "niece/nephew"),
        lambda x: x.replace("sibling's partner's child", "niece/nephew"),
        lambda x: x.replace("parent's niece/nephew", "cousin"),
        lambda x: x.replace("aunt/uncle's child", "cousin"),
        lambda x: x.replace("niece/nephew's sibling", "niece/nephew"),
    ]
    post_operations = [
        lambda x: FamilyTreeMember.relation_simplify_simple(x, "child"),
        lambda x: FamilyTreeMember.relation_simplify_simple(x, "parent"),
        lambda x: x.replace("grandsibling", "great aunt/uncle"),
    ]


    def __init__(self, discord_id:int, children:list, parent_id:int, partner_id:int):
        self.id = discord_id
        self._children = children
        self._parent = parent_id
        self._partner = partner_id
        self.tree_id = get_random_string()
        self.all_users[self.id] = self


    @staticmethod
    def relation_simplify_simple(string:str, search_string:str) -> str:
        '''
        Simplifies down a range of "child's child's child's..." to one set of "[great...] grandchild

        Params:
            string: str
                The string to be searched and modified
            search_string: str
                The name to be searched for and expanded upon
        '''

        # Split it to be able to iterate through
        split = string.strip().split(' ')
        new_string = ''
        counter = 0
        for i in split:
            if i in [f"{search_string}'s", search_string]:
                counter += 1
            elif counter == 1:
                new_string += f"{search_string}'s {i} "
                counter = 0
            elif counter == 2:
                new_string += f"grand{search_string}'s {i} "
                counter = 0
            elif counter > 2:
                new_string += f"{'great ' * (counter - 2)}grand{search_string}'s {i} "
                counter = 0
            else:
                new_string += i + ' '

        # And repeat again for outside of the loop
        if counter == 1:
            new_string += f"{search_string}'s "
            counter = 0
        elif counter == 2:
            new_string += f"grand{search_string}'s "
            counter = 0
        elif counter > 2:
            new_string += f"{'great ' * (counter - 2)}grand{search_string}'s"
            counter = 0

        # Return new string
        new_string = new_string.strip()
        if new_string.endswith("'s"):
            return new_string[:-2]
        return new_string

    
    def __repr__(self):
        return f"FamilyTreeMember[{self.id}]"


    @property
    def partner(self):
        return self.get(self._partner)


    @property
    def parent(self):
        return self.get(self._parent)


    @property
    def children(self):
        return [self.get(i) for i in self._children]


    @property
    def is_empty(self):
        return len(self.children) == 0 and self.parent == None and self.partner == None


    def destroy(self):
        if self.partner:
            self.partner._partner = None 
        if self.parent:
            self.parent._children.remove(self.id)
        for child in self.children:
            child._parent = None 
        del self.all_users[self.id]


    def get_name(self, bot):
        x = self.NAME_SUBSTITUTION.sub("_", unidecode(str(bot.get_user(self.id))))
        if len(x) <= 5:
            x = self.NAME_SUBSTITUTION.sub("_", str(bot.get_user(self.id)))
        return x


    @classmethod
    def remove_blank_profiles(cls):
        '''
        Removes blank/useless profiles from the cache
        '''

        for discord_id, tree_member in cls.all_users.items():
            if tree_member == None:
                continue
            if tree_member.is_empty:
                del cls.all_users[discord_id]


    @classmethod
    def get(cls, user_id:User):
        '''
        Gets a FamilyTreeMember object for the given user
        '''

        try:
            return cls.all_users[user_id]
        except KeyError:
            x = cls(user_id, [], None, None)
            cls.all_users[user_id] = x
            return x


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
        if expand_upwards and add_parent and self.parent:
            people_list = self.parent.span(people_list, add_parent=True, expand_upwards=expand_upwards, guild=guild)

        # Add your children
        if self.children:
            for child in self.children:
                people_list = child.span(people_list, add_parent=False, expand_upwards=expand_upwards, guild=guild)

        # Add your partner
        if self.partner:
            people_list = self.partner.span(people_list, add_parent=True, expand_upwards=expand_upwards, guild=guild)

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

        root_user = self
        already_processed = []
        while True:
            if root_user in already_processed:
                return root_user
            already_processed.append(root_user)
            if guild:
                if root_user.parent and guild.get_member(root_user.parent.id):
                    root_user = root_user.parent
                elif root_user.partner and guild.get_member(root_user.partner.id) and root_user.partner.parent and guild.get_member(root_user.partner.parent.id):
                    root_user = root_user.partner.parent
                else:
                    return root_user
            else:
                if root_user.parent:
                    root_user = root_user.parent
                elif root_user.partner and root_user.partner.parent:
                    root_user = root_user.partner.parent
                else:
                    return root_user


    def get_relation(self, other):
        '''
        Gets the relationship between two users, shortening it to a readable amount of text
        '''

        x = self.get_unshortened_relation(other)
        if not x:
            return None 
        for i in range(10):
            for o in self.operations:
                x = o(x)
        for o in self.post_operations:
            x = o(x)
        return x

    
    def get_unshortened_relation(self, other, working_relation:list=None, added_already:list=None) -> str:
        '''
        Gets your relation to the other given user or None
        '''

        if working_relation == None:
            working_relation = []
        if added_already == None:
            added_already = []
        if self in added_already:
            return None
        if other == self:
            ret_string = "'s ".join(working_relation)
            return ret_string

        added_already.append(self)

        if self.parent and self.parent not in added_already:
            x = self.parent.get_unshortened_relation(other, working_relation=working_relation+['parent'], added_already=added_already)
            if x: return x 
        if self.partner and self.partner not in added_already:
            x = self.partner.get_unshortened_relation(other, working_relation=working_relation+['partner'], added_already=added_already)
            if x: return x 
        if self.children:
            for i in [o for o in self.children if o not in added_already]:
                x = i.get_unshortened_relation(other, working_relation=working_relation+['child'], added_already=added_already)
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
            working_text = [
                f'0 @I{i.tree_id}@ INDI',
                f'\t1 NAME {i.get_name(bot)}'
            ]

            # If you have a parent, get added to their family
            if i.parent:
                if i.parent.id in family_id_cache:
                    working_text.append(f'\t1 FAMC @F{family_id_cache[i.parent.id]}@')
                elif i.parent.partner and i.parent.partner.id in family_id_cache:
                    working_text.append(f'\t1 FAMC @F{family_id_cache[i.parent.partner.id]}@')
                else:
                    working_text.append(f'\t1 FAMC @F{i.parent.tree_id}@')

            # If you have children or a partner, generate a family
            if i.children or i.partner:
                # current_text = '\n'.join(gedcom_text)

                # See if you need to make a new family or be added to one already made
                try:
                    insert_location = gedcom_text.index(f'\t1 HUSB @I{i.tree_id}@')
                    # Above will throw error if this user is not in a tree already

                    working_text.append(f'\t1 FAMS @F{family_id_cache[i.partner.id]}@')
                    family_id_cache[i.id] = i.partner.tree_id
                    for c in i.children:
                        gedcom_text.insert(insert_location, f'\t1 CHIL @I{c.tree_id}@')
                except ValueError:
                    family_id_cache[i.id] = i.tree_id
                    working_text.append(f'\t1 FAMS @F{i.tree_id}@')
                    working_text.append(f'0 @F{i.tree_id}@ FAM')
                    working_text.append(f'\t1 WIFE @I{i.tree_id}@')
                    if i.partner:
                        working_text.append(f'\t1 HUSB @I{i.partner.tree_id}@')
                    for c in i.children:
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
        if self in all_people:
            return people_dict
        if recursive_depth >= 500:
            return people_dict
        all_people.append(self)

        # Filter out non-guild members
        if guild:
            if not guild.get_member(self.id):
                return people_dict

        # Add to dict
        x = people_dict.get(depth, list())
        x.append(self)
        people_dict[depth] = x

        # Add your children
        if self.children:
            for child in self.children:
                people_dict = child.generational_span(people_dict, depth=depth+1, add_parent=False, expand_upwards=expand_upwards, guild=guild, all_people=all_people, recursive_depth=recursive_depth+1)

        # Add your partner
        if self.partner:
            people_dict = self.partner.generational_span(people_dict, depth=depth, add_parent=True, expand_upwards=expand_upwards, guild=guild, all_people=all_people, recursive_depth=recursive_depth+1)

        # Add your parent
        if expand_upwards and add_parent and self.parent:
            people_dict = self.parent.generational_span(people_dict, depth=depth-1, add_parent=True, expand_upwards=expand_upwards, guild=guild, all_people=all_people, recursive_depth=recursive_depth+1)

        # Remove dupes, should they be in there
        return people_dict


    def to_dot_script(self, bot, guild:Guild=None) -> str:
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
        gen_span = root_user.generational_span(guild=guild)
        # gen_span = root_user.generational_span(guild=guild, expand_upwards=True, add_parent=True)
        return self.to_dot_script_from_generational_span(gen_span)

    
    def to_full_dot_script(self, bot) -> str:
        '''
        Gives you the string of the FULL current family
        '''

        # Get the generation spanning tree
        root_user = self.get_root()
        # gen_span = root_user.generational_span(guild=guild)
        gen_span = root_user.generational_span(expand_upwards=True, add_parent=True)
        return self.to_dot_script_from_generational_span(gen_span)


    def to_dot_script_from_generational_span(self, gen_span:dict) -> str:
        '''
        Generates the DOT script from a given generational span
        '''

        ctu = CustomisedTreeUser.get(self.id)

        # Find my own depth
        my_depth = None
        for depth, l in gen_span.items():
            if self in l:
                my_depth = depth
                break

        # Add my partner and parent 
        if self.partner and self.partner not in gen_span.get(my_depth, list()):
            x = gen_span.get(my_depth, list())
            x.append(self.partner)
            gen_span[my_depth] = x
        if self.parent and self.parent not in gen_span.get(my_depth-1, list()):
            x = gen_span.get(my_depth-1, list())
            x.append(self.parent)
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
        user_parent_tree = {}  # Parent: random_string
        for generation in gen_span.values():
            for i in generation:
                all_users.append(i)
                if i == self:
                    all_text.append(f'\t{i.id}[label="{i.get_name(bot)}", fillcolor={ctu.hex["highlighted_node"]}, fontcolor={ctu.hex["highlighted_font"]}];')
                else:
                    all_text.append(f'\t{i.id}[label="{i.get_name(bot)}"];')
        
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
                user_parent_tree[person] = person.id
                added_already.append(person)
                if previous_person:
                    all_text.append(f"\t\t{previous_person.id} -> {person.id} [style=invis];")
                if person.partner and person.partner in generation:
                    user_parent_tree[person.partner] = user_parent_tree[person] = get_random_string()
                    all_text.append(f"\t\t{person.id} -> {user_parent_tree[person]} -> {person.partner.id};")
                    all_text.append(f"\t\t{user_parent_tree[person]} {self.INVISIBLE}")
                    added_already.append(person.partner)
                    previous_person = person.partner
                else:
                    all_text.append(f"\t\t{person.id};")
                    previous_person = person
            all_text.append("\t}")

            # Add the connecting node from parent to child
            all_text.append("\t{")
            for person in generation:
                if person.children and any([i in all_users for i in person.children]):
                    all_text.append(f"\t\th{user_parent_tree[person]} {self.INVISIBLE};")
            all_text.append("\t}")

            # Add the lines from parent to node to child
            added_already.clear()
            for person in generation:
                if person.children and any([i in all_users for i in person.children]):
                    if user_parent_tree[person] in added_already:
                        pass
                    else:
                        all_text.append(f"\t\t{user_parent_tree[person]} -> h{user_parent_tree[person]};")
                        added_already.append(user_parent_tree[person])
                    for child in [i for i in person.children if i in all_users]:
                        all_text.append(f"\t\th{user_parent_tree[person]} -> {child.id};")
        all_text.append("}")

        return '\n'.join(all_text)
