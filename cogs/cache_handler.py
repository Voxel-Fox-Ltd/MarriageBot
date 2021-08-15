import concurrent.futures as cf
import functools

import voxelbotutils as vbu

from cogs import utils


class CacheHandler(vbu.Cog):

    @staticmethod
    def handle_partner(row):
        utils.FamilyTreeMember(
            discord_id=row['user_id'],
            children=[],
            parent_id=None,
            partner_id=row['partner_id'],
            guild_id=row['guild_id'],
        )

    @staticmethod
    def handle_parent(row):
        parent = utils.FamilyTreeMember.get(row['parent_id'], row['guild_id'])
        parent._children.append(row['child_id'])
        child = utils.FamilyTreeMember.get(row['child_id'], row['guild_id'])
        child._parent = row['parent_id']

    async def cache_setup(self, db):
        """
        Set up the cache for the users.
        """

        # Get family data from database
        try:
            if self.bot.config['is_server_specific']:
                partnerships = await db("SELECT * FROM marriages WHERE guild_id<>0")
                parents = await db("SELECT * FROM parents WHERE guild_id<>0")
            else:
                partnerships = await db("SELECT * FROM marriages WHERE guild_id=0")
                parents = await db("SELECT * FROM parents WHERE guild_id=0")
        except Exception as e:
            self.logger.critical(f"Ran into an error selecting either marriages or parents: {e}", exc_info=e)
            exit(1)

        # Clear the current cache
        self.logger.info("Clearing the cache of all family tree members")
        utils.FamilyTreeMember.all_users.clear()

        # Cache the family data - partners
        self.logger.info(f"Caching {len(partnerships)} partnerships from partnerships")
        for i in partnerships:
            self.handle_partner(dict(i))

        # - children
        self.logger.info(f"Caching {len(parents)} parents/children from parents")
        for i in parents:
            self.handle_parent(dict(i))

        # And done
        self.logger.info("Family tree member caching complete")
        return True


def setup(bot: vbu.Bot):
    x = CacheHandler(bot)
    bot.add_cog(x)
