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

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import asyncpg

__all__ = (
    'get_names',
    'mint',
)


def mint(*x: Any) -> tuple[int, ...]:
    """
    Multi-int a list of items.
    """

    return tuple(int(i) for i in x)


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
