class Person(object):
    '''
    Representation of a person

    Attrs:
        name : str
            The name of the user
        id : str
            The ID of the user - kept as a string so stays truthy
        households : list
            List of households this person belongs to
    '''

    def __init__(self, information:str):
        information = information.strip()
        self.attr = {}
        self.parents = []
        self.households = []
        self.id = ''
        self.colour = 'white'
        self.name = ''

        self.name, attr_str = information[0:-1].split('(')  # Split at the parenthesis
        self.name = self.name.strip()
        attr_list = map(lambda x: x.strip(), attr_str.split(','))
        for a in attr_list:
            if '=' in a:
                k, v = a.split('=')
                self.attr[k] = v
            else:
                self.attr[a] = True
        self.id = self.attr['id']
        if 'F' in self.attr: self.colour = 'bisque'

    def graphviz(self):
        label = self.name
        opts = [f'label="{label}"']
        opts.append('style=filled')
        opts.append(f'fillcolor={self.colour}')
        return self.id + '[' + ', '.join(opts) + ']'
