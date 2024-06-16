"""
Copyright (c) Kae Bartlett

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from typing_extensions import Self

if TYPE_CHECKING:
    import asyncpg

__all__ = (
    'CustomTree',
)


class CustomTree:

    DEFAULT_COLOURS = {
        "edge": 0,
        "node": 0,
        "font": 0xFFFFFF,
        "highlighted_font": 0xFFFFFF,
        "highlighted_node": 0x0000FF,
        "background": 0xFFFFFF,
        "direction": "TB",
    }

    def __init__(
            self,
            user_id: int,
            *,
            edge: int | None = None,
            node: int | None = None,
            font: int | None = None,
            highlighted_font: int | None = None,
            highlighted_node: int | None = None,
            background: int | None = None,
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
    async def fetch(cls, conn: asyncpg.Connection, user_id: int) -> Self:
        """
        Get a user's custom tree colours.
        """

        row = await conn.fetchrow(
            """
            SELECT
                user_id,
                edge,
                node,
                font,
                highlighted_font,
                highlighted_node,
                background,
                direction
            FROM
                customisation
            WHERE
                user_id = $1
            """,
            user_id,
        )
        if not row:
            return cls(user_id)
        return cls(
            user_id,
            edge=row.get("edge"),
            node=row.get("node"),
            font=row.get("font"),
            highlighted_font=row.get("highlighted_font"),
            highlighted_node=row.get("highlighted_node"),
            background=row.get("background"),
            direction=row.get("direction"),
        )

    @property
    def hex(self) -> dict:
        """
        The conversion of the user's data into some quotes hex strings
        that can be passed directly to Graphviz.

        Provides deafults.
        """

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
            v = getattr(self, i, self.DEFAULT_COLOURS[i])
            if v is None:
                v = self.DEFAULT_COLOURS[i]
            if isinstance(v, int) and v < 0:
                v = "transparent"
            elif isinstance(v, int):
                v = f'"#{v:0>6X}"'
            ret[i] = v
        ret["direction"] = f'"{self.direction}"'
        return ret
