from io import TextIOWrapper
from discord import Guild
from discord.ext.commands import Context
from cogs.utils.family_tree.household import Household
from cogs.utils.family_tree.person import Person
from cogs.utils.family_tree.family_tree_member import FamilyTreeMember


class Family(object):
    '''
    Represents the whole family

    Attrs:
        everybody : dict
            A dictionary of every person in an {id: Person} pair
        households : list
            A list of household objects
    '''


    INVISIBLE = '[shape=circle, label="", height=0.01, width=0.01]'


    def __init__(self):
        self.everybody = {}
        self.households = []


    def add_person(self, information:str):
        '''
        Adds a person to self.everybody or updates their info if they already exist
        '''

        # Make the person
        person = Person(information)

        # Save their [new] information
        if person.id in self.everybody:
            self.everybody[person.id].attrs.update(person.attrs)
        else:
            self.everybody[person.id] = person

        # Return the person object
        return self.everybody[person.id]


    def add_household(self, household:Household):
        '''
        Adds a union (household) to self.households, and updates the
        family members infos about this union.
        '''

        # Allow only two-person unions
        # if len(household.parents) != 2:
        #     raise Exception('Number of parents != 2')

        # Assign it an ID
        household.id = len(self.households)
        self.households.append(household)

        # Add the household to the person's household attr
        for person in household.parents:
            if not household in person.households:
                person.households.append(household)


    def find_person(self, name:str):
        '''
        Tries to find a person matching the 'name' argument.
        '''

        # Search by id
        if name in self.everybody:
            return self.everybody[name]

        # Search by name
        try:
            return [i for i in self.everybody.values() if i.name == name][0]
        except IndexError:
            return None
        

    def populate(self, text:str):
        '''
        Reads the input file line by line to find people and unions
        '''

        household = Household()
        lines = text.strip().split('\n') + ['']
        for line in lines:
            line = line.rstrip()  # Only strip the right - maintain in case of child
            
            # Empty line - indicates new family coming up
            if line == '':
                if not household.is_empty:
                    self.add_household(household)
                household = Household()

            # Comment
            elif line[0] == '#':
                continue

            # Parent or child - investigate further
            else:
                # Indentation means child - this will always be called after parents
                if line[0] == '\t' or line[0:4] == '    ':
                    person = self.add_person(line.strip())
                    person.parents = household.parents
                    household.children.append(person)
                # Parent
                else:
                    person = self.add_person(line)
                    household.parents.append(person)
        
        # Add household if the working one isn't empty
        if not household.is_empty:
            self.add_household(household)


    def find_first_ancestor(self):
        '''
        Returns the first ancestor found

        A person is considered an ancestor if he/she has no parents

        This function is not very good, because we can have many persons with
        no parents, it will always return the first found. A better practice
        would be to return the one with the highest number of descendants
        '''

        for p in self.everybody.values():
            if len(p.parents) == 0:
                return p


    def next_generation(self, generation:list):
        '''
        Takes in a list of Person objects and outputs a list of their children
        '''

        next_gen = []

        for person in generation:
            for household in person.households:
                next_gen.extend(household.children)
        return next_gen


    @staticmethod
    def get_partner(household:Household, person:Person):
        '''
        Returns the spouse of a person in a union
        '''

        # Because these classes are truthy objects, they'll be returned as true
        # What's happening here is the first thing is run (household.parents[0] == person), so if that's true,
        # the second part (and household.parents[1]) will be returned since it always evaluates to true, and that's how
        # Python works. Otherwise, it'll return the other parent (or household.parents[0])
        try:
            return household.parents[0] == person and household.parents[1] or household.parents[0]
        except IndexError:
            return None


    def output_generation(self, generation:list) -> list:
        '''
        Gets an entire generation in DOT format
        Returns a list of lines to be output
        '''

        all_text = []

        # Display persons
        all_text.append('\t{ rank=same;')
        
        previous_person = None  # So we can put them next to each other
        for person in generation:
            household_count = len(person.households)

            if previous_person != None:
                all_text.append(f'\t\t{previous_person} -> {person.id} [style=invis];')

            # No partner? No point finishing this loop - just go back to the top
            if household_count == 0:
                previous_person = person.id
                continue
                
            household = person.households[0]
            spouse = Family.get_partner(household, person)
            if spouse == None:
                # For one-person households
                if len(generation) in [0, 1]:
                    all_text.append(f'\t\t{person.id};')
                previous_person = person.id
                continue
            else:
                all_text.append(f'\t\t{person.id} -> {spouse.id};')
                # all_text.append(f'\t\t{person.id} -> h{household.id} -> {spouse.id};')
                # all_text.append(f'\t\th{household.id}{self.INVISIBLE};')
                previous_person = spouse.id
        all_text.append('\t}')

        # Display lines below households
        all_text.append('\t{ rank=same;')
        previous_node = None
        for person in generation:
            for household in person.households:

                # Don't bother if they have no children
                if len(household.children) == 0:
                    continue

                # Go through each child and add lines for their children
                for parent, sub_id in zip(household.parents, 'abcdefghijklmnopqrstuvwxyz'):
                    # Get the children, skip if none
                    children = [i for i in household.children if i.attrs['parent']==parent.id]
                    child_count = len(children)
                    if child_count == 0:
                        continue

                    # Add link to previous to keep in line
                    if previous_node != None:
                        all_text.append(f'\t\t{previous_node} -> h{household.id}_{sub_id}_0 [style=invis];')

                    # Add a node to keep symmetry
                    if child_count % 2 == 0:
                        child_count += 1

                    # Draw links between nodes
                    all_text.append('\t\t' + ' -> '.join(map(lambda x: f'h{household.id}_{sub_id}_{x}', range(child_count))) + ';')

                    # Make the nodes invisible
                    for i in range(child_count):
                        all_text.append(f'\t\th{household.id}_{sub_id}_{i}{self.INVISIBLE};')
                        previous_node = f'h{household.id}_{sub_id}_{i}'

        all_text.append('\t}')

        # Draw lines to children from household lines
        for person in generation:
            for household in person.households:

                # Go through each parent and add lines to their children
                for parent, sub_id in zip(household.parents, 'abcdefghijklmnopqrstuvwxyz'):
                    # Get the children, skip if none
                    children = [i for i in household.children if i.attrs['parent']==parent.id]
                    child_count = len(children)
                    if child_count == 0:
                        continue

                    # Link parent to their children line
                    all_text.append(f'\t\t{parent.id} -> h{household.id}_{sub_id}_{int(child_count/2)};')

                    # Draw lines from children line to child
                    i = 0
                    for child in children:
                        all_text.append(f'\t\th{household.id}_{sub_id}_{i} -> {child.id};')
                        i += 1
                        if i == child_count/2:
                            i += 1

        return all_text


    def output_descending_tree(self, ancestor:Person):
        '''
		Outputs the whole descending family tree from a given ancestor,
        in DOT format.
		'''

        # Find the first household
        gen = [ancestor]

		# Print the start of a dot file
        all_text = [] 
        all_text.append('digraph {\n\tnode [shape=box];\n\tedge [dir=none];\n')

		# Go through every person and print them into the file,
		# listing a label, and colour
        for p in self.everybody.values():
            all_text.append('\t' + p.graphviz() + ';')
        all_text.append('')

		# Go through each generation and print it out
        while gen:
            all_text.extend(self.output_generation(gen))
            gen = self.next_generation(gen)

        all_text.append('}')
        return '\n'.join(all_text)


    @classmethod
    def get_full_tree(cls, ctx:Context, tree:FamilyTreeMember, all_guilds:bool) -> str:

        # Create the family
        family = cls()

        # Populate the family
        if all_guilds == True: 
            guild = None 
        else:
            guild = ctx.guild
        family.populate(tree.to_tree_string(ctx.bot, guild=guild))

        # Find the ancestor from whom the tree is built
        ancestor = family.find_first_ancestor()

        # Output the graph descriptor, in DOT format
        return family.output_descending_tree(ancestor)
