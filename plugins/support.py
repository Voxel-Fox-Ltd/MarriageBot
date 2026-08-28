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

import itertools
import os

import dotenv
import novus as n
from novus import types as t
from novus.ext import client
from novus.ext import database as db

from . import utils as u

dotenv.load_dotenv()


class Support(client.Plugin):

    support = client.CommandDescription(
        dm_permission=False,
        default_member_permissions=n.Permissions(manage_members=True),
        guild_ids=[int(i) for i in os.getenv("SUPPORT_GUILD_ID", "").split(",") if i]
    )

    @client.command(
        name="support copy-family-to-guild",
        options=[
            n.ApplicationCommandOption(
                "user",
                "The user who you want to copy the family of.",
                n.ApplicationOptionType.USER,
            ),
            n.ApplicationCommandOption(
                "guild_id",
                "The ID of the guild where the family should be copied to.",
                n.ApplicationOptionType.STRING,
            ),
            n.ApplicationCommandOption(
                "delete",
                "Whether all family members associated with that guild ID should be deleted.",
                n.ApplicationOptionType.BOOLEAN,
            ),
        ],
    )
    async def copyfamilytoguild(
            self,
            ctx: t.CommandGI,
            user: n.User,
            guild_id: str,
            delete: bool = False) -> None:
        """
        Copy a family to a Gold guild.
        """

        try:
            guild_idi = int(guild_id)
        except ValueError:
            raise Exception()
        if guild_idi <= 1e6:
            raise Exception()

        await ctx.defer()
        family_member = u.FamilyMember.get(user.id, 0)
        gen_span = family_member.generation_span(deep=True)
        generations = [i async for i in gen_span]
        all_users = list(itertools.chain.from_iterable(generations))

        parents: list[tuple[int, int, int]] = []  # child, parent, guild_id
        marriages: list[tuple[int, int, int]] = []  # user, partner, guild_id (Python-sorted; lowest user ID first)

        for f in all_users:
            for p in f._partner_ids:
                temp: tuple[int, int, int] = (min([f.id, p]), max([f.id, p]), guild_idi)
                if temp not in marriages:
                    marriages.append(temp)
            for c in f._child_ids:
                temp: tuple[int, int, int] = (c, f.id, guild_idi)
                if temp not in parents:
                    parents.append(temp)
            if f._parent_id:
                temp: tuple[int, int, int] = (f.id, f._parent_id, guild_idi)
                if temp not in parents:
                    parents.append(temp)

        async with db.Database.acquire() as conn:
            tr = conn.transaction()
            await tr.start()
            try:
                if delete:
                    await conn.execute("DELETE FROM parents WHERE guild_id=$1", guild_idi)
                    await conn.execute("DELETE FROM marriages WHERE guild_id=$1", guild_idi)
                await conn.copy_records_to_table(
                    "parents",
                    records=parents,
                    columns=["child_id", "parent_id", "guild_id"]
                )
                await conn.copy_records_to_table(
                    "marriages",
                    records=parents,
                    columns=["user_id", "partner_id", "guild_id"]
                )
                await tr.commit()
            except Exception as e:
                await tr.rollback()
                await ctx.send(f"Failed to copy over records.\n`{e}`")
                return

        await ctx.send(f"Done; copied over **{len(all_users):,}** family users. Relevant bot cache will need refreshing.")

    @client.command(
        name="support reload-cache",
    )
    async def reloadcache(self, ctx: t.CommandGI) -> None:
        """
        Reload the bot's family user cache.
        """

        if (cache := self.bot.get_plugin("CacheHandler")) is None:
            raise SystemExit("Could not get cache handler plugin.")

        await ctx.defer()
        await cache.on_load()
        v = len(u.FamilyMember.ALL_MEMBERS)
        await ctx.send(f"Reload successful; **{v:,}** family users loaded into cache.")

    @client.command(
        name="support check-user",
        options=[
            n.ApplicationCommandOption(
                "user",
                "The user that you want to check the roles/permissions of.",
                n.ApplicationOptionType.USER,
            ),
            n.ApplicationCommandOption(
                "guild_id",
                "The ID of the guild that you want to check the user in.",
                n.ApplicationOptionType.STRING,
            ),
        ],
    )
    async def checkuser(self, ctx: t.CommandGI, user: n.User, guild_id: str) -> None:
        """
        Grab information for a guild and a user within it.
        """

        await ctx.defer()
        guild = await n.Guild.fetch(self.state, guild_id)
        member = await guild.fetch_member(user.id)
        roles = await guild.fetch_roles()
        member_roles = [i for i in roles if i.id in member.role_ids]
        columns = [
            list(),
            list(),
            list(),
        ]
        for idx, (name, val) in enumerate(member.permissions.walk()):
            columns[idx % 3].append(f"{'🟢' if val else '🔴'} {name}")
        embed = (
            n.Embed()
            .update(title=guild.name)
            .set_image(guild.icon.get_url())
            .add_field("Roles", "\n".join([i.name for i in member_roles]))
            .add_field("Permissions 1", "\n".join(columns[0]))
            .add_field("Permissions 2", "\n".join(columns[1]))
            .add_field("Permissions 3", "\n".join(columns[2]))
        )
        await ctx.send(embeds=[embed])
