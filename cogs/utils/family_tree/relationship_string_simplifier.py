import re


class RelationshipStringSimplifier(object):
    """
    A general static class for simplifying a list of relations from
    a set of two users.
    """

    # Operations to cut down reduncencies
    pre_operations = [
        lambda x: x.replace("parent's partner", "parent"),
        lambda x: x.replace("partner's child", "child"),
        lambda x: x.replace("child's parent", ""),
        lambda x: x.replace(" 's", ""),
        lambda x: x.replace("  ", " "),
        lambda x: x if not x.startswith("'s") else x[2:],  # Strip out leading `'s`
        lambda x: x.strip(),  # Strip leading and trailing whitespace
    ]

    # Operations to replace phrases ("parent's child") with others ("sibling")
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

    # Operations to shorten strings of the same word ("child's child") into more appropriate forms ("grandchild")
    short_operations = [
        lambda x: re.sub(r"((?:child's )+)child", lambda m: ("great " * (m.group(1).count(" ") - 1)) + "grandchild", x),
        lambda x: re.sub(r"((?:parent's )+)parent", lambda m: ("great " * (m.group(1).count(" ") - 1)) + "grandparent", x),
        lambda x: x.replace("grandsibling", "great aunt/uncle"),
        lambda x: re.sub(r"sibling's (\d+(?:st|nd|rd|th) cousin)", r"\1", x),
    ]

    # Operations to strip out anything that shouldn't really be there, eg double spaces or trailing whitepsace
    post_operations = [
        lambda x: x.replace(" 's", ""),
        lambda x: x.replace("  ", " "),
        lambda x: x if not x.startswith("'s") else x[2:],
        lambda x: x.strip(),
    ]

    # Get all the regex ready
    cousin_matcher = re.compile(r"(?:parent's)(?: (?:parent|child)(?:'s)?)+ child")

    @classmethod
    def get_cousin_string(cls, k) -> str:
        """
        Gets the full cousin string.
        """

        p = k.group(0).count('parent')  # p = cls.get_cousin_parent_count(k)  # parent
        c = k.group(0).count('child')  # c = cls.get_cousin_child_count(k)  # child

        if p < 2:
            # Make sure we're not just working on nieces/children/siblings
            return k.group(0)
        if c == 1:
            # This is a variation on aunt/uncle
            if p <= 2:
                return "aunt/uncle"
            return f"{'great ' * (p - 3)} grand aunt/uncle"

        p -= 2
        c -= 2
        x = c + 1 if (c + 1) < p + 1 else p + 1  # nth cousin
        y = abs(p - c)  # y times removed

        if x < 1:
            return k.group(0)
        if x == 1 and y == 0:
            return "cousin"
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
            return cousin_string.strip()
        return (cousin_string + {True: "1 time removed", False: f"{y} times removed"}[y == 1]).strip()

    @classmethod
    def simplify(cls, string:str) -> str:
        """
        Runs the given input through the shortening operations a number of times so as to shorten the input to a nice
        family relationship string.
        """

        for _ in range(5):
            for o in cls.pre_operations:
                string = o(string)
        string = cls.cousin_matcher.sub(cls.get_cousin_string, string)
        for o in cls.operations:
            string = o(string)
        for o in cls.short_operations:
            string = o(string)
        for o in cls.post_operations:
            string = o(string)
        for o in cls.short_operations:
            string = o(string)
        return string
