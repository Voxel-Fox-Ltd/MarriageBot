class Simplifier(object):

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
        lambda x: Simplifier.relation_simplify_simple(x, "child"),
        lambda x: Simplifier.relation_simplify_simple(x, "parent"),
        lambda x: x.replace("grandsibling", "great aunt/uncle"),
    ]


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


    @classmethod 
    def simplify(self, string:str):
        return string
