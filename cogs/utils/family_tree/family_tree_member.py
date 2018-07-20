from discord import User


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

    def __init__(self, discord_id:int, children:list, parent_id:int, partner_id:int):
        self.id = discord_id
        self.children = children
        self.parent = parent_id
        self.partner = partner_id
        self.all_users[self.id] = self

    def get_partner(self):
        return self.get(self.partner)

    def get_parent(self):
        return self.get(self.parent)

    def get_children(self):
        return [self.get(i) for i in self.children]

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

    def span(self, people_list:list=None, add_parent:bool=False, expand_upwards:bool=False) -> list:
        '''
        Gets a list of every user related to this one

        Params:
            people_list: list 
                The list of users who are currently in the tree (so as to avoid recursion)
            add_parent: bool
                Whether or not to add the parent of this user to the people list
            expand_upwards: bool
                Whether or not to expand upwards in the tree

        Returns:
            A list of all people on the family for this user, in no particular order
        '''

        # Don't add yourself again
        if people_list == None:
            people_list = []
        if self in people_list:
            return people_list
        people_list.append(self)

        # Add your parent
        if expand_upwards and add_parent and self.parent:
            people_list = self.get_parent().span(people_list, add_parent=True, expand_upwards=expand_upwards)

        # Add your children
        if self.children:
            for child in self.get_children():
                if child in people_list:
                    continue
                people_list = child.span(people_list, add_parent=False, expand_upwards=expand_upwards)

        # Add your partner
        if self.partner:
            people_list = self.get_partner().span(people_list, add_parent=True, expand_upwards=expand_upwards)

        # Remove dupes, should they be in there
        nodupe = []
        for i in people_list:
            if i in nodupe:
                continue
            nodupe.append(i)
        return nodupe

    def expand_backwards(self, depth:int=1):
        '''
        Expands backwards into the tree

        Params: 
            depth: int = 1
                How far back to expand
                Set to -1 for the base root
        '''

        root_user = self
        while depth != 0:
            if root_user.parent:
                root_user = root_user.get_parent()
            elif root_user.partner and root_user.get_partner().parent:
                root_user = root_user.get_partner().get_parent()
            else:
                break
            depth -= 1
        return root_user

    def to_tree_string(self, bot, expand_backwards:int=0):
        '''
        Gives you a string of the current family tree that will go through familytreemaker.py

        Params:
            bot: CustomBot
                Used solely to get the names of people
            expand_backwards:int = 0
                See how far back you want to go up the generations
                Set to -1 for maximum
        '''

        fulltext = ''
        added_to_tree = []  # list of IDs that have been added
        nonecount = 0

        root_user = self.expand_backwards(expand_backwards)

        # Go through all who are related
        for user in root_user.span():

            # If you have nothing to add, you won't be added
            if user.partner == None and len(user.children) == 0:
                continue
            if user.id in added_to_tree:
                continue

            # Add the current iteration
            fulltext += user.get_name(bot) + f' (id={user.id})\n'

            # Add their partner
            if user.partner:
                fulltext += user.get_partner().get_name(bot) + f' (id={user.partner})\n'
                added_to_tree.append(user.partner)
            if len(user.children) > 0 and user.partner == None:
                fulltext += f'None (id={nonecount})\n'
                nonecount += 1

            # Add their children
            if len(user.children) > 0:
                for child in user.get_children():
                    fulltext += '\t' + child.get_name(bot) + f' (id={child.id})\n'
            if user.partner and len(user.get_partner().children) > 0:
                for child in user.get_partner().get_children():
                    fulltext += '\t' + child.get_name(bot) + f' (id={child.id})\n'

            # Cache user
            added_to_tree.append(user.id)
            fulltext += '\n'

        # Return text, changing the colour of the root post
        return root_user, fulltext.replace(f'(id={self.id})', f"(F, id={self.id})")

    def get_name(self, bot):
        return str(bot.get_user(self.id))
