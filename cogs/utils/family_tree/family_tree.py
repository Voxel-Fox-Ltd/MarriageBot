from cogs.utils.family_tree.family_tree_member import FamilyTreeMember


class FamilyTree(object):
    '''
    Represents a family tree object
    Should be a representation of a family

    Params:
        root: int
            The root user's Discord ID
        depth: int
            The depth that the tree should span
    '''

    def __init__(self, root:int, depth:int=3, original_root:int=None):
        self.root_id = root
        self.original_root = original_root if original_root else root
        self.root = None
        self.depth = depth

    async def populate_tree(self, database):
        '''
        Populates the family tree
        '''

        self.root = await FamilyTreeMember.generate(self.root_id, self.depth, database=database)

    def stringify(self, bot):
        '''
        Turns the family tree into a big long-ol string
        '''

        fulltext = ''
        added_to_tree = []  # list of IDs that have been added
        nonecount = 0

        for user in self.root.span([]):
            if user.partner == None and len(user.children) == 0:
                continue
            if user.id in added_to_tree:
                continue
            fulltext += user.get_name(bot) + f' (id={user.id})\n'
            if user.partner:
                fulltext += user.partner.get_name(bot) + f' (id={user.partner.id})\n'
                added_to_tree.append(user.partner.id)
            if len(user.children) > 0 and user.partner == None:
                fulltext += f'None (id={nonecount})\n'
                nonecount += 1
            if len(user.children) > 0:
                for child in user.children:
                    fulltext += '\t' + child.get_name(bot) + f' (id={child.id})\n'
            if user.partner and len(user.partner.children) > 0:
                for child in user.partner.children:
                    fulltext += '\t' + child.get_name(bot) + f' (id={child.id})\n'
            added_to_tree.append(user.id)
            fulltext += '\n'
        return fulltext.replace(f'(id={self.original_root})', f"(F, id={self.original_root})")

    def get_member(self, discord_id):
        '''
        Returns the the family tree member object of the given Discord ID should it exist,
        otherwise None
        '''

        for user in self.root.span([], include_parents=True, add_parent=True):
            if user.id == discord_id:
                return user
        return None

