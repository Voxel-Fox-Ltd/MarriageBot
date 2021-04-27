import voxelbotutils as utils

from cogs import utils as localutils


class CacheHandler(utils.Cog):

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
            self.logger.critical(f"Ran into an error selecting either marriages or parents: {e}")
            exit(1)

        # Clear the current cache
        self.logger.info(f"Clearing the cache of all family tree members")
        localutils.FamilyTreeMember.all_users.clear()

        # Cache the family data - partners
        self.logger.info(f"Caching {len(partnerships)} partnerships from partnerships")
        for i in partnerships:
            localutils.FamilyTreeMember(discord_id=i['user_id'], children=[], parent_id=None, partner_id=i['partner_id'], guild_id=i['guild_id'])

        # - children
        self.logger.info(f"Caching {len(parents)} parents/children from parents")
        for i in parents:
            parent = localutils.FamilyTreeMember.get(i['parent_id'], i['guild_id'])
            parent._children.append(i['child_id'])
            child = localutils.FamilyTreeMember.get(i['child_id'], i['guild_id'])
            child._parent = i['parent_id']

        # And done
        return True


def setup(bot:utils.Bot):
    x = CacheHandler(bot)
    bot.add_cog(x)
