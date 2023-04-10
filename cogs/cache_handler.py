from __future__ import annotations

from typing import List
import asyncio

import discord
from discord.ext import vbu

from cogs import utils
from cogs.utils import types


async def aiterator(iterable):
    for i in iterable:
        await asyncio.sleep(0)
        yield i


class CacheHandler(vbu.Cog[types.Bot]):

    async def recache_user(
            self,
            ftm: utils.FamilyTreeMember,
            db: vbu.Database | None = None):
        """
        Grab a user from the database and re-read them into cache.
        This does not handle the people attached to that user (eg
        adding this user to the parent's list of children, etc)
        """

        # Get a cached person
        if db is None:
            _db = await vbu.Database.get_connection()
        else:
            _db = db
        # await _db.call(
        #     """
        #     DELETE FROM
        #         marriages
        #     WHERE
        #         user_id = partner_id
        #     """,
        # )
        partnerships = await _db.call(
            """
            SELECT
                *
            FROM
                marriages
            WHERE
                (
                    user_id = $1
                    OR partner_id = $1
                )
                AND guild_id = $2
                AND user_id < partner_id  -- don't delete old data for now
            """,
            ftm.id, ftm._guild_id,
        )
        # await _db.call(
        #     """
        #     DELETE FROM
        #         parents
        #     WHERE
        #         parent_id = child_id
        #     """,
        # )
        parents = await _db.call(
            """
            SELECT
                *
            FROM
                parents
            WHERE
                child_id = $1
            AND
                guild_id = $2
            """,
            ftm.id, ftm._guild_id,
        )
        children = await _db.call(
            """
            SELECT
                *
            FROM
                parents
            WHERE
                parent_id = $1
            AND
                guild_id = $2
            """,
            ftm.id, ftm._guild_id,
        )
        if db is not None:
            await _db.disconnect()

        # Add children
        ftm.children = [r['child_id'] for r in children]

        # Add partners
        partner_ids = set()
        async for p in aiterator(partnerships):
            partner_ids.update((p['user_id'], p['partner_id'],))
        while ftm.id in partner_ids:
            partner_ids.remove(ftm.id)
        ftm.partners = list(partner_ids)

        # Add parent
        if parents:
            ftm._parent = parents[0]['parent_id']

    @vbu.Cog.listener("on_recache_user")
    async def _recache_user(
            self,
            user: discord.User | discord.Member,
            guild_id: int = 0):
        self.logger.info(
            "Asked to recache user ID %s (guild ID %s)",
            user.id, guild_id,
        )
        ftm = utils.FamilyTreeMember.get(user.id, guild_id)
        changed_users: list[utils.FamilyTreeMember] = []
        async with vbu.Database() as db:
            for uf in ftm.span():
                changed_users.append(uf)
                await self.recache_user(uf, db)
        async with vbu.Redis() as re:
            for uf in changed_users:
                await re.publish("TreeMemberUpdate", uf.to_json())

    @staticmethod
    def handle_partner(row: types.MarriagesDB):
        user = utils.FamilyTreeMember.get(row['user_id'], row['guild_id'])
        partner = user.add_partner(row['partner_id'], return_added=True)
        partner.add_partner(user)

    @staticmethod
    def handle_parent(row: types.ParentageDB):
        parent = utils.FamilyTreeMember.get(row['parent_id'], row['guild_id'])
        child = parent.add_child(row['child_id'], return_added=True)
        child.parent = row['parent_id']

    async def cache_setup(self, db: vbu.Database):
        """
        Set up the cache for the users.
        """

        # Get family data from database
        where: str
        if self.bot.config['is_server_specific']:
            where = "guild_id <> 0"
        else:
            where = "guild_id = 0"
        try:
            partnerships: List[types.MarriagesDB] = await db(
                """
                SELECT
                    *
                FROM
                    marriages
                WHERE
                    {0}
                    AND user_id > partner_id
                """.format(where),
            )
            parents: List[types.ParentageDB] = await db(
                """
                SELECT
                    *
                FROM
                    parents
                WHERE
                    {0}
                """.format(where),
            )
        except Exception as e:
            self.logger.critical(
                (
                    f"Ran into an error selecting either "
                    f"marriages or parents: {e}"
                ),
                exc_info=e,
            )
            exit(1)

        # Clear the current cache
        self.logger.info("Clearing the cache of all family tree members")
        utils.FamilyTreeMember.all_users.clear()

        # Cache the family data - partners
        self.logger.info(f"Caching {len(partnerships)} partnerships from partnerships")
        async for i in aiterator(partnerships):
            self.handle_partner(i)

        # - children
        self.logger.info(f"Caching {len(parents)} parents/children from parents")
        async for i in aiterator(parents):
            self.handle_parent(i)

        # And done
        self.logger.info("Family tree member caching complete")
        return True


def setup(bot: types.Bot):
    x = CacheHandler(bot)
    bot.add_cog(x)
