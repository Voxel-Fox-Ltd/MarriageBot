from __future__ import annotations

from typing import Literal, Optional

from discord.ext import vbu


__all__ = (
    'CustomisedTreeUser',
)


class CustomisedTreeUser:
    """
    A class to hold the custom tree setup for a given user.
    """

    __slots__ = (
        'id',
        'edge',
        'node',
        'font',
        'highlighted_font',
        'highlighted_node',
        'background',
        'direction',
    )

    def __init__(
            self,
            user_id: int,
            *,
            edge: Optional[int] = None,
            node: Optional[int] = None,
            font: Optional[int] = None,
            highlighted_font: Optional[int] = None,
            highlighted_node: Optional[int] = None,
            background: Optional[int] = None,
            direction: Literal["TB", "LR"] = "TB"):
        self.id = user_id
        self.edge = edge
        self.node = node
        self.font = font
        self.highlighted_font = highlighted_font
        self.highlighted_node = highlighted_node
        self.background = background
        self.direction = direction

    @classmethod
    async def fetch_by_id(
            cls,
            db: vbu.Database,
            user_id: int) -> CustomisedTreeUser:
        """
        Grabs a user's data from the database.
        """

        data = await db.call(
            """
            SELECT
                *
            FROM
                customisation
            WHERE
                user_id = $1
            """,
            user_id,
        )
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

        # Get our defaults
        default_hex = self.get_default_hex()

        # Get our attrs
        attrs = (
            "edge",
            "font",
            "node",
            "highlighted_font",
            "highlighted_node",
            "background",
        )

        # Fill up a dict
        ret = {}
        for i in attrs:
            v = getattr(self, i)
            if v is None:
                v = default_hex[i]
            elif v <= 0:
                v = "transparent"
            else:
                v = f'"#{v:X}"'
            ret[i] = v
        ret["direction"] = self.direction

        # And return
        return ret

    @property
    def unquoted_hex(self) -> dict:
        """
        The same as self.hex, but strips out the quote marks from the items.
        Pretty much directly passed into a website's CSS.
        """

        # Just strip the quote marks from the items
        return {
            i: o.strip('"')
            for i, o
            in self.hex.items()
        }

    @staticmethod
    def get_default_hex() -> dict:
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

        return {
            i: o.strip('"')
            for i, o
            in cls.get_default_hex().items()
        }

    async def save(
            self,
            db: vbu.Database):
        """
        Saves the cached data from this object into the database.
        """

        await db(
            """
            INSERT INTO
                customisation
                (
                    user_id,
                    edge,
                    node,
                    font,
                    highlighted_font,
                    highlighted_node,
                    background,
                    direction
                )
            VALUES
                (
                    $1,  -- user_id
                    $2,  -- edge
                    $3,  -- node
                    $4,  -- font
                    $5,  -- highlighted_font
                    $6,  -- highlighted_node
                    $7,  -- background
                    $8  -- direction
                )
            ON CONFLICT (user_id)
            DO UPDATE
            SET
                edge = excluded.edge,
                node = excluded.node,
                font = excluded.font,
                highlighted_font = excluded.highlighted_font,
                highlighted_node = excluded.highlighted_node,
                background = excluded.background,
                direction = excluded.direction
            """,
            self.id, self.edge, self.node, self.font,
            self.highlighted_font, self.highlighted_node,
            self.background, self.direction,
        )
