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

import asyncio
import random
from typing import TYPE_CHECKING, Any

import novus as n
from novus.ext.database import database as db

if TYPE_CHECKING:
    import asyncpg
    from novus.ext import client

__all__ = (
    "get_name",
    "get_names",
    "mint",
    "get_guild_id",
    "e",
    "get_command_mention",
    "get_upsell_button",
    "get_upsell_row",
    "get_upsell_components",
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


async def get_guild_id(bot: client.Client, ctx: n.Interaction, log=None) -> int:
    """
    Get the relevant guild ID for the current running instance of the bot.
    """

    log.debug(0.1)
    if bot.config.gold and ctx.guild:
        return ctx.guild.id
    log.debug(0.2)
    if ctx.guild:
        log.debug(0.3)
        async with db.Database.acquire() as conn:
            log.debug(0.4)
            try:
                log.debug(0.5)
                guild_specific: bool | None = await asyncio.wait_for(
                    conn.fetchval(
                        "SELECT guild_specific_families FROM guild_settings WHERE guild_id=$1",
                        ctx.guild.id,
                    ),
                    timeout=2.0,
                )
                log.debug(0.6)
            except asyncio.TimeoutError:
                log.debug(0.7)
                guild_specific = None
        log.debug(0.8)
        if guild_specific is None or guild_specific is False:
            log.debug(0.9)
            return 0
        log.debug(0.11)
        return ctx.guild.id
    log.debug(0.12)
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


def get_command_mention(bot: client.Client, command_name: str) -> str:
    """
    Get the mention for a command, or a string representing it.
    """

    command = bot.get_command(command_name)
    if command is None:
        return f"`/{command_name}`"
    else:
        return command.mention


def get_upsell_button(
        ctx: n.Interaction | None = None,
        *,
        gold: bool = False) -> n.Button:
    """
    Get a button that links to the MarriageBot store.
    """

    if gold:
        label = "Get MarriageBot Gold"
        if ctx:
            label = ctx._("Get MarriageBot Gold")
    else:
        label = "Get MarriageBot perks"
        if ctx:
            label = ctx._("Get MarriageBot perks")
    return n.Button(
        label=label,
        style=n.ButtonStyle.LINK,
        url="https://voxelfox.co.uk/portal/marriagebot",
        custom_id="PERKS_MB_DISCARD_____"
    )


def get_upsell_row(
        ctx: n.Interaction | None = None,
        *,
        gold: bool = False) -> n.ActionRow:
    return n.ActionRow([get_upsell_button(ctx, gold=gold)])


def get_upsell_components(
        ctx: n.Interaction | None = None,
        *,
        gold: bool = False) -> list[n.ActionRow]:
    return [get_upsell_row(ctx, gold=gold)]
