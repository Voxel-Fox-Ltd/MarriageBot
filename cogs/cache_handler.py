from __future__ import annotations
from typing import List

import discord
from discord.ext import vbu

from cogs import utils
from cogs.utils import types


class CacheHandler(vbu.Cog[types.Bot]):

    async def recache_user(
            self,
            user: discord.abc.Snowflake,
            guild_id: int = 0):
        """
        Grab a user from the database and re-read them into cache.
        This does not handle the people attached to that user (eg
        adding this user to the parent's list of children, etc)
        """

        # Get a cached person
        ftm = utils.FamilyTreeMember.get(user.id, guild_id)
        async with vbu.Database() as db:
            partnerships = await db(
                """
                SELECT
                    *
                FROM
                    marriages
                WHERE
                    (
                        user_id = $1
                    OR
                        partner_id = $1
                    )
                AND
                    guild_id = $2
                AND
                    user_id > partner_id  -- don't delete old data for now
                """,
                ftm.id, ftm._guild_id,
            )
            parents = await db(
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
            children = await db(
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

        # Add children
        ftm.children = [r['child_id'] for r in children]

        # Add partners
        partner_ids = set()
        for p in partnerships:
            partner_ids.update((p['user_id'], p['partner_id'],))
        while ftm.id in partner_ids:
            partner_ids.remove(ftm.id)
        ftm.partners = list(partner_ids)

        # Add parent
        if parents:
            ftm._parent = parents[0]['parent_id']

    @vbu.Cog.listener("on_recache_user")
    async def _recache_user(self, user, guild_id):
        await self.recache_user(user, guild_id)

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
                AND
                    user_id > partner_id
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
        for i in partnerships:
            self.handle_partner(i)

        # - children
        self.logger.info(f"Caching {len(parents)} parents/children from parents")
        for i in parents:
            self.handle_parent(i)

        # And done
        self.logger.info("Family tree member caching complete")
        return True


def setup(bot: types.Bot):
    x = CacheHandler(bot)
    bot.add_cog(x)
