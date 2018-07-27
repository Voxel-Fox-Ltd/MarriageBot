from re import compile
from random import choice
from discord import User, File


generate_id = lambda: ''.join([choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for i in range(10)])


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
    substitution = compile(r'[^\x00-\x7F\x80-\xFF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF]')


    def __init__(self, discord_id:int, children:list, parent_id:int, partner_id:int):
        self.id = discord_id
        self.tree_id = generate_id()
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

    def span(self, people_list:list=None, add_parent:bool=False, expand_upwards:bool=False, depth:int=0, max_depth:int=None) -> list:
        '''
        Gets a list of every user related to this one
        If "add_parent" and "expand_upwards" are True, then it should add every user in a given tree,
        even if they're related through marriage's parents etc

        Params:
            people_list: list 
                The list of users who are currently in the tree (so as to avoid recursion)
            add_parent: bool
                Whether or not to add the parent of this user to the people list
            expand_upwards: bool
                Whether or not to expand upwards in the tree
            depth: int = 0
                Starting depth of the span method
            max_depth: int = None
                How far to expand when making the tree

        Returns:
            A list of all people on the family for this user, in no particular order
        '''

        # Don't add yourself again
        if people_list == None:
            people_list = []
        if self in people_list:
            return people_list
        elif abs(depth) == max_depth:
            return people_list
        people_list.append(self)

        # Add your parent
        if expand_upwards and add_parent and self.parent:
            people_list = self.get_parent().span(people_list, add_parent=True, expand_upwards=expand_upwards, depth=depth+1, max_depth=max_depth)

        # Add your children
        if self.children:
            for child in self.get_children():
                if child in people_list:
                    continue
                people_list = child.span(people_list, add_parent=False, expand_upwards=expand_upwards, depth=depth-1, max_depth=max_depth)

        # Add your partner
        if self.partner:
            people_list = self.get_partner().span(people_list, add_parent=True, expand_upwards=expand_upwards, depth=depth, max_depth=max_depth)

        # Remove dupes, should they be in there
        nodupe = []
        for i in people_list:
            if i in nodupe:
                continue
            nodupe.append(i)
        return nodupe

    def expand_backwards(self, depth:int=1, all_guilds:bool=True, ctx=None):
        '''
        Expands backwards into the tree

        Params: 
            depth: int = 1
                How far back to expand
                Set to -1 for the base root
            all_guilds: bool = True
                Sets whether or not to get users from all guilds
            ctx: Context = None
                Used to check whether a user is in the initial guild
                Only required if all_guilds is set to False
        '''

        previous = None
        root_user = self
        while depth != 0:
            previous = root_user
            if root_user.parent:
                root_user = root_user.get_parent()
            elif root_user.partner and root_user.get_partner().parent:
                root_user = root_user.get_partner().get_parent()
            else:
                break
            if all_guilds == False and ctx.guild.get_member(root_user.id) == None:
                root_user = previous
                break
            depth -= 1
        return root_user

    def generate_gedcom_file(self, bot):
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
                if i.parent in family_id_cache:
                    working_text.append(f'\t1 FAMC @F{family_id_cache[i.parent]}@')
                elif i.get_parent().partner and i.get_parent().partner in family_id_cache:
                    working_text.append(f'\t1 FAMC @F{family_id_cache[i.get_parent().partner]}@')
                else:
                    working_text.append(f'\t1 FAMC @F{i.get_parent().tree_id}@')

            # If you have children or a partner, generate a family
            if i.children or i.partner:
                current_text = '\n'.join(gedcom_text)

                # See if you need to make a new family or be added to one already made
                try:
                    insert_location = gedcom_text.index(f'\t1 HUSB @I{i.tree_id}@')
                    # Above will throw error if this user is not in a tree already

                    working_text.append(f'\t1 FAMS @F{family_id_cache[i.partner]}@')
                    family_id_cache[i.id] = i.get_partner().tree_id
                    for c in i.get_children():
                        gedcom_text.insert(insert_location, f'\t1 CHIL @I{c.tree_id}@')
                except ValueError:
                    family_id_cache[i.id] = i.tree_id
                    working_text.append(f'\t1 FAMS @F{i.tree_id}@')
                    working_text.append(f'0 @F{i.tree_id}@ FAM')
                    working_text.append(f'\t1 WIFE @I{i.tree_id}@')
                    if i.partner:
                        working_text.append(f'\t1 HUSB @I{i.get_partner().tree_id}@')
                    for c in i.get_children():
                        working_text.append(f'\t1 CHIL @I{c.tree_id}@')

            gedcom_text.extend(working_text)
        x = '0 HEAD\n\t1 GEDC\n\t\t2 VERS 5.5\n\t\t2 FORM LINEAGE-LINKED\n\t1 CHAR UNICODE\n' + '\n'.join(gedcom_text) + '\n0 TRLR'
        return x

    def to_tree_string(self, ctx, expand_backwards:int=0, depth:int=-1, all_guilds:bool=False):
        '''
        Gives you a string of the current family tree that will go through familytreemaker.py

        Params:
            ctx: Context
                Used solely to get the names of people
            expand_backwards: int = 0
                See how far back you want to go up the generations
                Set to -1 for maximum
            all_guilds: bool = False
                Decides whether to get users from all guilds or just the current guild to
                add to your tree
        '''

        fulltext = ''
        added_to_tree = []  # list of IDs that have been added
        nonecount = 0
        bot = ctx.bot
        initial_user = self.id

        if self.parent:
            root_user = self.get_parent()
        else:
            root_user = self
        root_user = root_user.expand_backwards(expand_backwards, all_guilds=all_guilds, ctx=ctx)

        # Go through all who are related
        for user in root_user.span(max_depth=depth):

            # If you have nothing to add, you won't be added
            if user.partner == None and len(user.children) == 0:
                # No partner, no children
                continue
            if user.id in added_to_tree:
                # Already added
                continue
            if initial_user in user.children:
                pass
            elif all_guilds == False:
                if ctx.guild.get_member(user.id) == None:
                    # Not in guild
                    continue
                elif user.parent and ctx.guild.get_member(user.parent) == None and user.id != initial_user:
                    # Parent not in guild
                    continue
                elif user.partner and user.id == initial_user:
                    # Have a partner, are initial user
                    pass
                elif ctx.guild.get_member(user.partner) == None and any([ctx.guild.get_member(i) for i in user.children]) == False:
                    # Family are all invalid
                    continue

            # Add the current iteration
            fulltext += user.get_name(bot).replace('(', '_').replace(')', '_') + f' (id={user.id})\n'

            # Add their partner
            if user.id == initial_user and user.partner:
                fulltext += user.get_partner().get_name(bot).replace('(', '_').replace(')', '_') + f' (id={user.partner})\n'
                added_to_tree.append(user.partner)
            elif all_guilds == False and user.partner and ctx.guild.get_member(user.partner) != None:
                # Partner exists in server
                fulltext += user.get_partner().get_name(bot).replace('(', '_').replace(')', '_') + f' (id={user.partner})\n'
                added_to_tree.append(user.partner)
            elif all_guilds == False and user.partner:
                # Partner not in server
                added_to_tree.append(user.partner)
            elif all_guilds and user.partner:
                # Partner exists
                fulltext += user.get_partner().get_name(bot).replace('(', '_').replace(')', '_') + f' (id={user.partner})\n'
                added_to_tree.append(user.partner)

            if all_guilds == False and any([ctx.guild.get_member(i) for i in user.children]) and user.id == initial_user and user.partner == None:
                # No spouse, children, is initial
                fulltext += f'None (id={nonecount})\n'
                nonecount += 1
            if all_guilds == False and any([ctx.guild.get_member(i) for i in user.children]) and (ctx.guild.get_member(user.partner) == None and user.id != initial_user):
                # Valid children and invalid spouse
                fulltext += f'None (id={nonecount})\n'
                nonecount += 1
            elif all_guilds and len(user.children) > 0 and user.partner == None:
                # Any amount of children, no spouse
                fulltext += f'None (id={nonecount})\n'
                nonecount += 1

            # Add their children
            if all_guilds == False:
                # Get valid children from selection
                valid_children = [o.id for o in [ctx.guild.get_member(i) for i in user.children] if o]
                # Add them to the tree
                if len(valid_children) > 0:
                    for child in [self.get(i) for i in valid_children]:
                        fulltext += '\t' + child.get_name(bot).replace('(', '_').replace(')', '_') + f' (id={child.id})\n'
                # If their spouse is valid with children
                if ctx.guild.get_member(user.partner) and len(user.get_partner().children) > 0:
                    # Add their children
                    valid_children = [o.id for o in [ctx.guild.get_member(i) for i in user.get_partner().children] if o]
                    for child in [self.get(i) for i in valid_children]:
                        fulltext += '\t' + child.get_name(bot).replace('(', '_').replace(')', '_') + f' (id={child.id})\n'
            elif all_guilds:
                if len(user.children) > 0:
                    for child in user.get_children():
                        fulltext += '\t' + child.get_name(bot).replace('(', '_').replace(')', '_') + f' (id={child.id})\n'
                if user.partner and len(user.get_partner().children) > 0:
                    for child in user.get_partner().get_children():
                        fulltext += '\t' + child.get_name(bot).replace('(', '_').replace(')', '_') + f' (id={child.id})\n'


            # Cache user
            added_to_tree.append(user.id)
            fulltext += '\n'

        # Return text, changing the colour of the root post
        return root_user, fulltext.replace(f'(id={self.id})', f"(F, id={self.id})")

    def get_name(self, bot):
        return self.substitution.sub('_', str(bot.get_user(self.id)))
