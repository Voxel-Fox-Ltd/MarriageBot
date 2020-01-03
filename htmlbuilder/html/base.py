class BaseHTMLNode(object):
    """A base HTML object"""

    def __init__(self, tag:str, content:str=None, **attrs):
        self.tag = tag
        self.content = content
        self.attrs = attrs
        self.children: list = []

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass

    def new_child(self, tag:str, content:str=None, **attrs) -> 'BaseHTMLNode':
        """Makes a new node and adds it to the current object's children"""

        child: self.__class__ = self.__class__(tag, content, **attrs)
        self.children.append(child)
        return child

    def __str__(self):
        """Turns the current object into a valid HTML object"""

        working = f"<{self.tag} "
        working += " ".join([f'{i.replace("class_", "class")}="{o}"' for i, o in self.attrs.items()])
        if self.children:
            working += ">"
            for i in self.children:
                working += str(i)
            working += f"</{self.tag}>"
        elif self.content:
            working += f">{self.content}</{self.tag}>"
        else:
            working += " />"
        return working
