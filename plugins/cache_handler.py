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

import novus as n
from novus import types as t
from novus.ext import client
from novus.ext import database as db

from . import utils as u

if TYPE_CHECKING:
    import asyncpg


class CacheHandler(client.Plugin):

    CACHE_LOG_NUMBER = 100_000

    async def fetch_partners(self) -> None:
        async with db.Database.acquire() as conn:
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
                    "Cached %.2f%% (%s of %s) partners",
                    counter / len(partner_rows) * 100, counter, len(partner_rows)
                )
        self.log.info("Cached %s partners", counter)

    async def fetch_parents(self) -> None:
        async with db.Database.acquire() as conn:
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
                    "Cached %.2f%% (%s of %s) children",
                    counter / len(child_rows) * 100, counter, len(child_rows)
                )
        self.log.info("Cached %s children", counter)

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
        await conn.close()

        await asyncio.wait([
            asyncio.create_task(self.fetch_partners()),
            asyncio.create_task(self.fetch_parents()),
        ])
        self.log.info("Cached %s total users", len(u.FamilyMember.ALL_MEMBERS))

    @client.loop(10)
    async def get_name_loop(self) -> None:
        """
        Loop the util set of missing names to add them to the database.
        """

        if not u.missing_user_names:
            return

        # threadsafe loop through u.missing_user_names, fetch the id from discord, and store in db
        async with db.Database.acquire() as conn:
            for id in u.missing_user_names.copy():
                self.log.info("Fetching username for ID %s", id)
                try:
                    user = await n.User.fetch(self.state, id)
                except n.NotFound:
                    name = f"Deleted User[{id}]"
                except n.Forbidden:
                    name = f"Private User[{id}]"
                except n.HTTPException as e:
                    self.log.error("Failed to fetch user %s - %s", id, e)
                    await asyncio.sleep(60)  # just in case it was a rate limit
                    continue
                else:
                    name = str(user)
                if not name:
                    continue
                await conn.execute(
                    "INSERT INTO usernames (id, name) VALUES ($1, $2) "
                    "ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name",
                    id, name,
                )
                u.missing_user_names.discard(id)

    @client.event.command
    async def on_command(self, ctx: t.CommandI) -> None:
        """
        Save all names that the bot interacts with.
        """

        valid_names = {
            ctx.user.id: str(ctx.user),
        }
        for k, v in ctx.data.resolved.users.items():
            valid_names[k] = str(v)

        async with db.Database.acquire() as conn:
            for k, v in valid_names.items():
                await conn.execute(
                    """
                    INSERT INTO
                        usernames
                        (id, name)
                    VALUES
                        ($1, $2)
                    ON CONFLICT
                        (id)
                    DO UPDATE
                    SET
                        name = excluded.name
                    """,
                    k, v,
                )
