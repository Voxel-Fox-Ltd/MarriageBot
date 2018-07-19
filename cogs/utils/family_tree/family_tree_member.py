class FamilyTreeMember(object):
    '''
    A family member to go in the tree
    '''

    @classmethod
    async def generate(cls, discord_id:int, depth:int, database, already_in:list=None, generation:int=0):
        '''
        Generates the family information based on the given info
        '''

        if already_in == None:
            already_in = []
        for i in already_in:
            if i.id == discord_id:
                return i

        # Get children
        children = await database('SELECT * FROM parents WHERE parent_id=$1', discord_id)
        if children:
            children = [i['child_id'] for i in children]
            depthchildren = []
            if depth > 0:
                for child_id in children:
                    c = await cls.generate(discord_id=child_id, depth=depth-1, database=database, generation=generation-1)
                    depthchildren.append(c)
            else:
                for child_id in children:
                    c = cls(child_id, [], None, None, generation=generation-1)
            children = depthchildren
        else:
            children = []

        # Get parent
        parent = await database('SELECT * FROM parents WHERE child_id=$1', discord_id)
        if parent:
            parent = parent[0]['parent_id']
            if depth > 0:
                parent = await cls.generate(discord_id=parent, depth=depth-1, database=database, generation=generation+1)
            else:
                parent = cls(parent, [], None, None, generation=generation+1)
        else:
            parent = None

        # Get partner
        partner = await database('SELECT * FROM marriages WHERE user_id=$1 AND valid=TRUE', discord_id)
        if partner:
            partner = partner[0]['partner_id']
            if depth > 0:
                partner = await cls.generate(discord_id=partner, depth=depth-1, database=database, generation=generation)
            else:
                partner = cls(partner, [], None, None, generation=generation)
        else:
            partner = None

        # Return instance
        v = cls(discord_id, children, parent, partner, generation=generation)
        already_in.append(v)
        v.all_in_tree = already_in
        if depth <= 0:
            for child in v.children:
                child.parent = v
            if parent:
                parent.children = [v]
            if partner:
                partner.partner = v
        return v

    def __init__(self, discord_id:int, children:list, parent, partner, generation:int=0):
        self.id = discord_id
        self.children = children
        self.parent = parent
        self.partner = partner
        self.all_in_tree = []
        self.generation = generation

    def __str__(self):
        return f"<FamilyTreeMember of {self.id} ({len(self.children)} children, married to {self.partner!r})>"

    def __repr__(self):
        return str(self.id)

    def span(self, all_people, add_parent=False, include_parents:bool=False):
        '''
        Gets a list of every user in the tree
        '''

        # if self in all_people:
        #     return all_people
        # all_people.append(self)
        # if add_parent and self.parent:
        #     all_people = self.parent.span(all_people, add_parent=True)
        # if self.children:
        #     for child in self.children:
        #         all_people = child.span(all_people, add_parent=False)
        # if self.partner:
        #     all_people = self.partner.span(all_people, add_parent=True)

        if self in all_people:
            return all_people
        all_people.append(self)
        if include_parents and add_parent and self.parent:
            all_people = self.parent.span(all_people, add_parent=True, include_parents=include_parents)
        if self.children:
            for child in self.children:
                if child in all_people:
                    continue
                all_people = child.span(all_people, add_parent=False, include_parents=include_parents)
        if self.partner:
            all_people = self.partner.span(all_people, add_parent=True, include_parents=include_parents)

        nodupe = []
        for i in all_people:
            if i in nodupe:
                continue
            nodupe.append(i)
        return nodupe

    def get_name(self, bot):
        return str(bot.get_user(self.id))
