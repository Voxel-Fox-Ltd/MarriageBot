import voxelbotutils as vbu

from cogs import utils


class ChildIDConverter(vbu.converters.UserID):

    @classmethod
    async def convert(cls, ctx: vbu.Context, value: str):
        """
        A more gentle converter that accepts child names as well as pings and IDs.
        """

        # See if it's a ping or a mention
        try:
            return await super().convert(value)

        # See if it's a name
        except Exception as e:
            user_tree = utils.FamilyTreeMember.get(ctx.author.id, utils.get_family_guild_id(ctx))
            for child in user_tree.children:
                child_name = await utils.DiscordNameManager.fetch_name_by_id(ctx.bot, child.id)
                child_name_length = len(child_name)
                if len(value) == child_name_length or len(value) == len(child_name_length) - 4:
                    pass
                else:
                    raise
                if child_name.startswith(value):
                    return child.id
            raise e

