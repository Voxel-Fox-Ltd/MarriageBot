from voxelbotutils.cogs.utils.database import DatabaseConnection

class CustomisedTreeUser(object):
    """
    A class to hold the custom tree setup for a given user.
    """

    __slots__ = (
        'id', 'edge', 'node', 'font', 'highlighted_font',
        'highlighted_node', 'background', 'direction',
    )

    def __init__(
            self, user_id:int, *, edge:int=None, node:int=None, font:int=None, highlighted_font:int=None,
            highlighted_node:int=None, background:int=None, direction:str="TB"):
        self.id = user_id
        self.edge = edge
        self.node = node
        self.font = font
        self.highlighted_font = highlighted_font
        self.highlighted_node = highlighted_node
        self.background = background
        self.direction = direction

    @classmethod
    async def get(cls, db:DatabaseConnection, user_id:int) -> 'CustomisedTreeUser':
        """
        Grabs a user's data from the database.
        """

        data = await db('SELECT * FROM customisation WHERE user_id=$1', user_id)
        if data:
            return cls(**data[0])
        return cls(user_id)

    @property
    def hex(self) -> dict:
        """
        The conversion of the user's data into some quotes hex strings
        that can be passed directly to Graphviz.
        Provides deafults.
        """

        default_hex = self.get_default_hex()

        # Edgs
        if self.edge is not None:
            edge = f'"#{self.edge:06X}"' if self.edge >= 0 else 'transparent'
        else:
            edge = default_hex['edge']

        # Font colour
        if self.font is not None:
            font = f'"#{self.font:06X}"' if self.font >= 0 else 'transparent'
        else:
            font = default_hex['font']

        # Node background colour
        if self.node is not None:
            node = f'"#{self.node:06X}"' if self.node >= 0 else 'transparent'
        else:
            node = default_hex['node']

        # Highlighted node font colour
        if self.highlighted_font is not None:
            highlighted_font = f'"#{self.highlighted_font:06X}"' if self.highlighted_font >= 0 else 'transparent'
        else:
            highlighted_font = default_hex['highlighted_font']

        # Highlighted node background colour
        if self.highlighted_node is not None:
            highlighted_node = f'"#{self.highlighted_node:06X}"' if self.highlighted_node >= 0 else 'transparent'
        else:
            highlighted_node = default_hex['highlighted_node']

        # Background colour
        if self.background is not None:
            background = f'"#{self.background:06X}"' if self.background >= 0 else 'transparent'
        else:
            background = default_hex['background']

        # Return data
        return {
            'edge': edge,
            'node': node,
            'font': font,
            'highlighted_font': highlighted_font,
            'highlighted_node': highlighted_node,
            'background': background,
            'direction': f'"{self.direction}"',
        }

    @property
    def unquoted_hex(self) -> dict:
        """
        The same as self.hex, but strips out the quote marks from the items.
        Pretty much directly passed into a website's CSS.
        """

        # Just strip the quote marks from the items
        return {i: o.strip('"') for i, o in self.hex.items()}

    @classmethod
    def get_default_hex(self) -> dict:
        """
        The default hex codes that are used, quoted.
        """

        return {
            'edge': '"#000000"',
            'node': '"#000000"',
            'font': '"#FFFFFF"',
            'highlighted_font': '"#FFFFFF"',
            'highlighted_node': '"#0000FF"',
            'background': '"#FFFFFF"',
            'direction': '"TB"',
        }

    @classmethod
    def get_default_unquoted_hex(cls) -> dict:
        """
        The default hex codes that are used, unquoted. Pretty much directly passed into a website's CSS.
        """

        return {i: o.strip('"') for i, o in cls.get_default_hex().items()}

    async def save(self, db:DatabaseConnection):
        """
        Saves the cached data from this object into the database.
        """

        await db(
            """INSERT INTO customisation (user_id, edge, node, font, highlighted_font, highlighted_node, background, direction)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8) ON CONFLICT (user_id) DO UPDATE SET edge=excluded.edge, node=excluded.node,
            font=excluded.font, highlighted_font=excluded.highlighted_font, highlighted_node=excluded.highlighted_node,
            background=excluded.background, direction=excluded.direction""",
            self.id, self.edge, self.node, self.font, self.highlighted_font, self.highlighted_node, self.background, self.direction,
        )
