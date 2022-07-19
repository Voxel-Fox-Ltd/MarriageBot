from __future__ import annotations

import discord
from discord.ext import vbu

from cogs import utils


class CacheHandler(vbu.Cog[utils.types.Bot]):

    async def recache_user(
            self,
            user: discord.abc.Snowflake,
            guild_id: int = 0):
        """
        Grab a user from the database and re-read them into cache.
        """

        ftm = utils.FamilyTreeMember.get(user.id, guild_id)
        async with vbu.Database() as db:
            partnerships = await db(
                """
                SELECT
                    *
                FROM
                    marriages
                WHERE
                    user_id = $1
                AND
                    guild_id = $2
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
        ftm._children = [r['child_id'] for r in children]
        if partnerships:
            ftm._partner = partnerships[0]['partner_id']
        if parents:
            ftm._parent = parents[0]['parent_id']

    @vbu.Cog.listener("on_recache_user")
    async def _recache_user(self, user, guild_id):
        await self.recache_user(user, guild_id)

    @staticmethod
    def handle_partner(row):
        user = utils.FamilyTreeMember.get(row['user_id'], row['guild_id'])
        user.partner = row['partner_id']
        user.partner.partner = user  # type: ignore - Pyright doesn't like this completely valid code

    @staticmethod
    def handle_parent(row):
        parent = utils.FamilyTreeMember.get(row['parent_id'], row['guild_id'])
        parent.add_child(row['child_id'])
        child = utils.FamilyTreeMember.get(row['child_id'], row['guild_id'])
        child.parent = row['parent_id']

    async def cache_setup(self, db: vbu.Database):
        """
        Set up the cache for the users.
        """

        # Get family data from database
        try:
            if self.bot.config['is_server_specific']:
                partnerships = await db(
                    """
                    SELECT
                        *
                    FROM
                        marriages
                    WHERE
                        guild_id <> 0
                    """,
                )
                parents = await db(
                    """
                    SELECT
                        *
                    FROM
                        parents
                    WHERE
                        guild_id <> 0
                    """,
                )
            else:
                partnerships = await db(
                    """
                    SELECT
                        *
                    FROM
                        marriages
                    WHERE
                        guild_id = 0
                    """,
                )
                parents = await db(
                    """
                    SELECT
                        *
                    FROM
                        parents
                    WHERE
                        guild_id = 0
                    """,
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


def setup(bot: utils.types.Bot):
    x = CacheHandler(bot)
    bot.add_cog(x)
