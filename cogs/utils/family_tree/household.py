class Household(object):
    '''
    A representation of a union between two persons and their children
    '''

    def __init__(self):
        self.parents = []
        self.children = []
        self.id = 0

    @property
    def is_empty(self):
        if len(self.parents) == 0 and len(self.children) == 0:
            return True
        return False
