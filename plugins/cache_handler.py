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

from novus.ext import client
from novus.ext import database as db

from . import utils as u

if TYPE_CHECKING:
    import asyncpg


class CacheHandler(client.Plugin):

    CACHE_LOG_NUMBER = 100_000

    async def on_load(self) -> None:
        """
        Start the bot, get all rows, load into cache.
        """

        self.log.info("Starting cache process")
        if (loaded_db := self.bot.get_plugin("Database")) is None:
            raise SystemExit("Database not loaded before cache handler.")
        await loaded_db.loaded.wait()
        for _ in range(5):
            try:
                conn: asyncpg.Connection = await db.Database.pool.acquire()
                break
            except Exception as e:
                self.log.error("Couldn't open database connection - %s", e)
                await asyncio.sleep(1)
        else:
            raise SystemExit("Failed to cache any users")
        partner_rows = await conn.fetch(
            "SELECT * FROM marriages",
        )
        counter = 0
        for r in partner_rows:
            (
                u.FamilyMember
                .get(r["user_id"], guild_id=r["guild_id"])
                .add_partner(r["partner_id"])
            )
            await asyncio.sleep(0)
            counter += 1
            if counter % self.CACHE_LOG_NUMBER == 0:
                self.log.info(
                    "Cached %%%s (%s of %s) partners",
                    counter / len(partner_rows) * 100, counter, len(partner_rows)
                )
        self.log.info("Cached %s partners", counter)
        child_rows = await conn.fetch(
            "SELECT * FROM parents",
        )
        counter = 0
        for r in child_rows:
            (
                u.FamilyMember
                .get(r["child_id"], guild_id=r["guild_id"])
                .add_parent(r["parent_id"])
            )
            await asyncio.sleep(0)
            counter += 1
            if counter % self.CACHE_LOG_NUMBER == 0:
                self.log.info(
                    "Cached %%%s (%s of %s) children",
                    counter / len(child_rows) * 100, counter, len(child_rows)
                )
        self.log.info("Cached %s children", counter)
        await conn.close()
        self.log.info("Cached %s total users", len(u.FamilyMember.ALL_MEMBERS))
