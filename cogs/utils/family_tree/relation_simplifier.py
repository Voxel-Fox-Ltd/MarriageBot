from re import compile as _compile


class Simplifier(object):

    pre_operations = [
        lambda x: x.replace("parent's partner", "parent"),
        lambda x: x.replace("partner's child", "child"),
        # lambda x: x.replace("parent's child", ""),
        lambda x: x.replace("child's parent", ""),
        lambda x: x.replace(" 's", ""),
        lambda x: x.replace("  ", " "),
        lambda x: x if not x.startswith("'s") else x[2:],
        lambda x: x.strip(),
    ]
    operations = [
        lambda x: x.replace("parent's sibling", "aunt/uncle"),
        lambda x: x.replace("aunt/uncle's child", "cousin"),
        lambda x: x.replace("parent's child", "sibling"),
        lambda x: x.replace("sibling's child", "niece/nephew"),
        lambda x: x.replace("sibling's partner's child", "niece/nephew"),
        lambda x: x.replace("parent's niece/nephew", "cousin"),
        lambda x: x.replace("aunt/uncle's child", "cousin"),
        lambda x: x.replace("niece/nephew's sibling", "niece/nephew"),
        lambda x: x.replace("niece/nephew's child", "grandniece/nephew").replace("grandgrandniece/nephew", "great grandniece/nephew"),
    ]
    short_operations = [
        lambda x: Simplifier.relation_simplify_simple(x, "child"),
        lambda x: Simplifier.relation_simplify_simple(x, "parent"),
        # lambda x: Simplifier.relation_simplify_simple(x, "niece/nephew"),
        # lambda x: Simplifier.get_cousin_string(x),
        lambda x: x.replace("grandsibling", "great aunt/uncle"),
        lambda x: Simplifier.sibling_cousin_remover(x),
    ]
    post_operations = [
        lambda x: x.replace(" 's", ""),
        lambda x: x.replace("  ", " "),
        lambda x: x if not x.startswith("'s") else x[2:],
        lambda x: x.strip(),
    ]
    # cousin_matcher = _compile(r"(((great )*?)(grand)?(parent)'s )?(cousin)('s)? ?((((great )*? ?(grand)?)child('s)?)*)")  # magic
    cousin_matcher = _compile(r"(parent('s)?) (((parent('s)?)|(child('s)?)) ?)+($|(partner))")
    sibling_cousin_matcher = _compile(r"sibling's \d+((st)|(nd)|(rd)|(th)) cousin")
    nephew_child_matcher = _compile(r"(niece\/nephew's )((child('s )?)+)")


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
    def relation_simplify_nephew(cls, string:str) -> str:
        '''
        Simplifies down a range of "niece/nephew's child's childs..." to one set of "[great...] grandniece/nephew

        Params:
            string: str
                The string to be searched and modified
        '''

        # k = cls.nephew_child_matcher.search(string)
        # great_count = k.group(2).count(' ')
        # if 'child' in k.group(2):
        #     span = k.span()
        #     return string[:span[0]] + f"{'great ' * great_count}grandniece/nephew" + string[:span[1]]
        return string


    @staticmethod
    def get_cousin_parent_count(k):
        '''Gets the amount of generations UP the cousin count goes'''

        p = 0
        if k.group(3):
            # greats
            p += k.group(3).strip().count(' ')
        if k.group(4):
            # grand
            p += 1
        if k.group(5):
            # parent
            p += 1
        return p

    @staticmethod
    def get_cousin_child_count(k):
        '''Gets the amount of generations DOWN the cousin count goes'''

        # group 5 is cousin, so we get an extra space
        # group 7 is [child's child's...]
        # group 12 is GRAND-child
        return (k.group(6) + k.group(8)).strip().count(' ') + {True:1, False:0}[bool(k.group(12))]

    @classmethod
    def get_cousin_string(cls, string:str):
        '''Gets the full cousin string'''

        k = cls.cousin_matcher.search(string)
        if not k:
            return string
        # if k.group(0).startswith("parent's child"):
        #     span = k.span()
        #     return string[:span[0]] + " sibling's " + string[span[1]:]
        
        p = k.group(0).count('parent')  # p = cls.get_cousin_parent_count(k)  # parent 
        c = k.group(0).count('child')  # c = cls.get_cousin_child_count(k)  # child

        if p < 2:
            # Make sure we're not just working on nieces/children/siblings
            return string
        if c == 1:
            # This is a variation on aunt/uncle
            if p <= 2:
                return string[:k.span()[0]] + "aunt/uncle" + string[k.span()[1]:]
            return string[:k.span()[0]] + f"{'great ' * (p - 3)} grand aunt/uncle" + string[k.span()[1]:]

        p -= 2
        c -= 2
        x = c + 1 if (c + 1) < p + 1 else p + 1  # nth cousin
        y = abs(p - c)  # y times removed

        if x == 1 and y == 0:
            return string[:k.span()[0]] + "cousin" + string[k.span()[1]:]
        cousin_string = ""
        if str(x).endswith('1') and x != 11:
            cousin_string += f"{x}st cousin "
        elif str(x).endswith('2') and x != 12:
            cousin_string += f"{x}nd cousin "
        elif str(x).endswith('3') and x != 13:
            cousin_string += f"{x}rd cousin "
        else:
            cousin_string += f"{x}th cousin "
        if y == 0:
            return string[:k.span()[0]] + cousin_string.strip() + string[k.span()[1]:]
        return string[:k.span()[0]] + (cousin_string + {True: "1 time removed", False: f"{y} times removed"}[y==1]).strip() + string[k.span()[1]:]


    @classmethod
    def sibling_cousin_remover(cls, string:str):
        '''Removes "sibling's nth cousin" to "nth cousin"'''

        k = cls.sibling_cousin_matcher.search(string) 
        if not k:
            return string
        span = k.span()
        return string[:span[0]] + k.group(0).replace("sibling's ", "") + string[span[1]:]


    @classmethod 
    def simplify(cls, string:str):
        '''Runs the given input through the shortening operations
        a number of times so as to shorten the input to a nice
        family relationship string'''

        before = string
        for i in range(10):
            for o in cls.pre_operations:
                string = o(string) 
                if string == before:
                    continue 
                else:
                    before = string
        for i in range(5):
            string = cls.get_cousin_string(string)
            if string == before:
                continue 
            else:
                before = string
        for i in range(10):
            for o in cls.operations:
                string = o(string) 
                if string == before:
                    continue 
                else:
                    before = string
        for i in range(10):
            for o in cls.short_operations:
                string = o(string)
                if string == before:
                    continue 
                else:
                    before = string
        for i in range(10):
            for o in cls.post_operations:
                string = o(string) 
                if string == before:
                    continue 
                else:
                    before = string
        for i in range(10):
            for o in cls.short_operations:
                string = o(string)
                if string == before:
                    continue 
                else:
                    before = string
        return string
