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

from dataclasses import dataclass
from typing import Self

from cachetools import TTLCache, cached
from novus.ext.client import Client


@dataclass
class Perks:
    max_children: int = 5
    max_partners: int = 1
    can_run_fulltree: bool = False
    can_run_disownall: bool = False
    tree_command_cooldown: int = 60
    can_run_abandon: bool = False

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
    @cached(TTLCache(maxsize=2 ** 8, ttl=60 * 2))
    async def get_perks_for_user(cls, bot: Client, user_id: int) -> Self:
        """
        Get the perks for a given user from the Voxel Fox API.
        """

        # Override stuff for owners
        if user_id in bot.config.owner_ids:
            return cls.three()

        # If we gold we golden
        if bot.config.is_server_specific:
            return cls.three()

        # Check if they have a purchase
        async with bot.database() as db:
            rows = await db(
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
        if rows:
            return cls.three()

        # Check VFL purchases
        url = "https://voxelfox.co.uk/api/portal/check"
        params = {
            "product_id": "b6586947-0ce4-4b1c-bf27-6713b33409d3",
            "discord_user_id": user_id,
        }
        try:
            async with bot.session.get(url, params=params, timeout=3) as r:
                data = await r.json()
        except Exception:
            data = {}
        if data.get("success", False) and data.get("result"):
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
            return tier_mapping[tier]

        # Check Top.gg votes
        try:
            aw = bot.get_user_topgg_vote(user_id)
            data = await asyncio.wait_for(aw, timeout=3)
            if data:
                return TIER_VOTER
        except asyncio.TimeoutError:
            pass
        return tier_mapping[0]
