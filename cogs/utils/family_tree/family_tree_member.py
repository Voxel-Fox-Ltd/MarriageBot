from re import compile
from random import choice
from discord import User, File, Guild
from unidecode import unidecode


def generate_id():
    return ''.join([
        choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for i in range(10)
    ])


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
    substitution = compile(r'[^\x00-\x7F\x80-\xFF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF]|\"|\(|\)')


    def __init__(self, discord_id:int, children:list, parent_id:int, partner_id:int):
        self.id = discord_id
        self.tree_id = generate_id()
        self._children = children
        self._parent = parent_id
        self._partner = partner_id
        self.all_users[self.id] = self


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
            self.partner.partner = None 
        if self.parent:
            self.parent.children.remove(self.id)
        for child in self.children:
            child.parent = None 
        del self.all_users[self.id]


    def get_name(self, bot):
        x = self.substitution.sub("_", unidecode(str(bot.get_user(self.id))))
        if len(x) <= 5:
            x = self.substitution.sub("_", str(bot.get_user(self.id)))
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
            people_list = self.parent.span(people_list, add_parent=True,expand_upwards=expand_upwards)

        # Add your children
        if self.children:
            for child in self.children:
                people_list = child.span(people_list, add_parent=False, expand_upwards=expand_upwards)

        # Add your partner
        if self.partner:
            people_list = self.partner.span(people_list, add_parent=True,expand_upwards=expand_upwards)

        # Remove dupes, should they be in there
        nodupe = []
        for i in people_list:
            if i in nodupe:
                continue
            nodupe.append(i)
        return nodupe


    def get_root(self, guild:Guild=None):
        '''
        Expands backwards into the tree up to a root user
        Only goes up one line of family so it cannot add your spouse's parents etc

        Params: 
            guild: Guild = None
                If you want to get users only from a given guild, supply a guild here
        '''

        previous = None
        root_user = self
        while True:
            previous = root_user
            if root_user.parent:
                root_user = root_user.parent
            elif root_user.partner and root_user.partner.parent:
                root_user = root_user.partner.parent
            else:
                break
            if guild and guild.get_member(root_user.id) == None:
                root_user = previous
                break
        return root_user

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
                current_text = '\n'.join(gedcom_text)

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


    def to_tree_string(self, bot, guild:Guild=None) -> str:
        '''
        Gives you a string of the current family tree that will go through Family

        Params:
            bot: Bot
                Used solely to get the names of people
            guild: Guild = None
                If set to none, does nothing of interest. If set to a guild, will only add
                members to the tree that are in the given guild
        '''

        full_text = []  # list of lines
        added_to_tree = []  # list of IDs that have been added

        # Get the relevant root user
        if guild == None:
            root_user = self.get_root()
        else:
            root_user = self.get_root(guild=guild)

        # Get the right span
        if guild == None:
            span = root_user.span()
        else:
            span = root_user.span(guild=guild)

        # Iterate through all family members
        for user in span:

            # Only add people with relevance
            if user.partner == None and len(user.children) == 0:
                continue
            if user.id in added_to_tree:
                continue

            # Add a user, their spouse, and their children
            full_text.append(f"{user.get_name(bot)} (id={user.id})")
            added_to_tree.append(user.id)
            if user.partner:
                full_text.append(f"{user.partner.get_name(bot)} (id={user.partner.id})")
                added_to_tree.append(user.partner.id)
            children = user.children 
            if user.partner:
                children.extend(user.partner.children)
            for child in children:
                full_text.append(f"\t{child.get_name(bot)} (id={child.id})")
            full_text.append("")

        # Return text, changing the colour of the root post
        return '\n'.join(full_text).replace('\t', '    ').replace(f'(id={self.id})', f"(F, id={self.id})")
