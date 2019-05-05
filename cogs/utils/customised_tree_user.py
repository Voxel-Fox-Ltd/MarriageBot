class CustomisedTreeUser(object):

    all_users = {}  # discord_id: CTU
    bot = None

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
    async def get(cls, key):
        async with cls.bot.database() as db:
            data = await db('SELECT * FROM customisation WHERE user_id=$1', key)
        if data:
            return cls(**data[0])
        return cls(key)


    @property 
    def hex(self) -> dict:
        if self.edge != None:
            edge =  f'"#{self.edge:06X}"' if self.edge >= 0 else 'transparent'
        else:
            edge = '"#000000"'

        if self.font != None:
            font =  f'"#{self.font:06X}"' if self.font >= 0 else 'transparent'
        else:
            font = '"#000000"'

        if self.node != None:
            node =  f'"#{self.node:06X}"' if self.node >= 0 else 'transparent'
        else:
            node = '"#FFFFFF"'

        if self.highlighted_font != None:
            highlighted_font =  f'"#{self.highlighted_font:06X}"' if self.highlighted_font >= 0 else 'transparent'
        else:
            highlighted_font = '"#FFFFFF"'

        if self.highlighted_node != None:
            highlighted_node =  f'"#{self.highlighted_node:06X}"' if self.highlighted_node >= 0 else 'transparent'
        else:
            highlighted_node = '"#0000FF"'

        if self.background != None:
            background =  f'"#{self.background:06X}"' if self.background >= 0 else 'transparent'
        else:
            background = '"#FFFFFF"'

        return {
            'edge': edge,
            'node': node,
            'font': font,
            'highlighted_font': highlighted_font,
            'highlighted_node': highlighted_node,
            'background': background,
        }

    
    @property 
    def unquoted_hex(self):
        return {i: o.strip('"') for i, o in self.hex.items()}

    
    @classmethod 
    def get_default_hex(self):
        return {
            'edge': '"#000000"',
            'node': '"#000000"',
            'font': '"#FFFFFF"',
            'highlighted_font': '"#FFFFFF"',
            'highlighted_node': '"#0000FF"',
            'background': '"#FFFFFF"',
        }


    @classmethod 
    def get_default_unquoted_hex(self):
        return {i: o.strip('"') for i, o in self.hex.items()}
