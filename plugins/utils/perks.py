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
from typing import TYPE_CHECKING

import aiohttp
from cachetools import TTLCache
from novus.ext.database import database as db

from .utils import get_guild_id

if TYPE_CHECKING:
    import novus as n
    from novus.ext import client

__all__ = (
    "Perks",
)


class Perks:

    CACHE: dict[int, Perks] = TTLCache(maxsize=2 ** 8, ttl=60 * 2)  # pyright: ignore

    def __init__(
            self,
            max_children: int = 5,
            max_partners: int = 2,
            can_run_fulltree: bool = True,
            can_run_disownall: bool = False,
            tree_command_cooldown: int = 60,
            can_run_abandon: bool = False):
        self.max_children: int = max_children
        self.max_partners: int = max_partners
        self.can_run_fulltree: bool = can_run_fulltree
        self.can_run_disownall: bool = can_run_disownall
        self.tree_command_cooldown: int = tree_command_cooldown
        self.can_run_abandon: bool = can_run_abandon

    @classmethod
    def zero(cls):
        return cls()

    @classmethod
    def one(cls):
        return cls(
            max_children=10,
            can_run_disownall=True,
            tree_command_cooldown=15,
            max_partners=2,
        )

    @classmethod
    def two(cls):
        return cls(
            max_children=15,
            can_run_fulltree=True,
            can_run_disownall=True,
            can_run_abandon=True,
            tree_command_cooldown=15,
            max_partners=4,
        )

    @classmethod
    def three(cls):
        return cls(
            max_children=20,
            can_run_fulltree=True,
            can_run_disownall=True,
            can_run_abandon=True,
            tree_command_cooldown=5,
            max_partners=8,
        )

    @classmethod
    async def get_perks_for_user(
            cls,
            bot: client.Client,
            ctx: n.Interaction,
            user_id: int) -> Perks:
        """
        Get the perks for a given user from the VFL API.
        """

        # If the bot is Gold then simply let everyone do everything
        if await get_guild_id(bot, ctx) != 0:
            return cls.three()

        # If we're in the cache already we don't need to return anything
        if (cached := cls.CACHE.get(user_id)):
            return cached

        # Check if they have a purchase
        async with db.Database.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT
                    *
                FROM
                    guild_specific_families
                WHERE
                    purchased_by = $1
                """,
                user_id,
            )
        if row is not None:
            return cls.three()

        # Check VFL purchases for subscription
        url = "https://voxelfox.co.uk/api/portal/check"
        params = {
            "product_id": "b6586947-0ce4-4b1c-bf27-6713b33409d3",
            "discord_user_id": user_id,
        }
        try:
            async with aiohttp.ClientSession() as session:
                site = await asyncio.wait_for(session.get(url, params=params), timeout=3.0)
                data = await site.json()
        except Exception:
            data = {}
        if data.get("success", False) and data.get("result", False):
            purchase_item_ids = [
                i["product_id"]
                for i in data["purchases"]
            ]
            purchased_products = [
                data["products"][i]["product_name"]
                for i in purchase_item_ids
            ]
            tier = max([
                int(i.split(" ")[-1])
                for i in purchased_products
            ])
            return {
                1: cls.one,
                2: cls.two,
                3: cls.three,
            }[tier]()

        # # Check VFL purchases for Gold TEMPORARY
        # url = "https://voxelfox.co.uk/api/portal/check"
        # params = {
        #     "product_id": "854856f5-5d98-47c6-860d-64bcf2654e36",
        #     "discord_user_id": user_id,
        # }
        # try:
        #     async with aiohttp.ClientSession() as session:
        #         site = await asyncio.wait_for(session.get(url, params=params), timeout=3.0)
        #         data = await site.json()
        # except Exception:
        #     data = {}
        # if data.get("success", False) and data.get("result", False):
        #     return cls.three()

        # No purchase, return default
        return cls.zero()
