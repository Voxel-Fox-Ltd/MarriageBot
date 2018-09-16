class CustomisedTreeUser(object):

    all_users = {}  # discord_id: CTU

    def __init__(self, user_id:int, *, edge:int=None, node:int=None, font:int=None, highlighted_font:int=None, highlighted_node:int=None, background:int=None):
        self.id = user_id
        self.edge = edge
        self.node = node
        self.font = font
        self.highlighted_font = highlighted_font
        self.highlighted_node = highlighted_node
        self.background = background
        self.all_users[user_id] = self

    
    @classmethod
    def get(cls, key):
        try:
            return cls.all_users[key]
        except Exception:
            return cls(key)


    @property 
    def hex(self) -> dict:
        return {
            'edge': f'"#{self.edge:06X}"' if self.edge else 'white',
            'node': f'"#{self.node:06X}"' if self.node else 'black',
            'font': f'"#{self.font:06X}"' if self.font else 'white',
            'highlighted_font': f'"#{self.highlighted_font:06X}"' if self.highlighted_font else 'white',
            'highlighted_node': f'"#{self.highlighted_node:06X}"' if self.highlighted_node else 'dodgerblue4',
            'background': f'"#{self.background:06X}"' if self.background else 'transparent',
        }
