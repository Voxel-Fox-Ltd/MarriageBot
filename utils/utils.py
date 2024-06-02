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

import random
from typing import TYPE_CHECKING, Any

import novus as n

if TYPE_CHECKING:
    import asyncpg
    from novus.ext import client

__all__ = (
    'get_name',
    'get_names',
    'mint',
    'get_guild_id',
    'e',
)


def mint(*x: Any) -> tuple[int, ...]:
    """
    Multi-int a list of items.
    """

    return tuple(int(i) for i in x)


async def get_name(conn: asyncpg.Connection | asyncpg.Pool, id: int) -> str:
    """
    Get a single name from the database.
    """

    res = await get_names(conn, id)
    return res[id]


async def get_names(
        conn: asyncpg.Connection | asyncpg.Pool,
        *ids: int) -> dict[int, str]:
    """
    Get names from the database.
    """

    rows = await conn.fetch(
        "SELECT * FROM usernames WHERE id = ANY($1::BIGINT[])",
        ids,
    )
    base = {i: f"User[{i}]" for i in ids}
    for r in rows:
        base[r["id"]] = r["name"]
    return base


def get_guild_id(bot: client.Client, ctx: n.Interaction) -> int:
    """
    Get the relevant guild ID for the current running instance of the bot.
    """

    if ctx.guild:
        return ctx.guild.id if bot.config.gold else 0
    return 0


def e(content: str, image_url: str | None = None) -> list[n.Embed]:
    """
    Take a string and shove it into an embed.
    """

    e = (
        n.Embed(
            color=random.randint(0x0, 0xFFFFFF),
            description=content,
        )
        .set_footer("Thanks for using MarriageBot :)")
    )
    if image_url:
        e.set_image(image_url)
    return [e]
