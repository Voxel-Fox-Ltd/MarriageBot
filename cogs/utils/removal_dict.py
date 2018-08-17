class RemovalDict(dict):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def remove(self, element):
        try:
            return self.pop(element)
        except KeyError:
            return None            
