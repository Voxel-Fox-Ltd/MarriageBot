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

from novus import types as t
from novus.ext import client
from novus.ext import database as db


class NameHandler(client.Plugin):

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
