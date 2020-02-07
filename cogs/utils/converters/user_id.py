import discord
from discord.ext import commands

from cogs.utils.family_tree.family_tree_member import FamilyTreeMember


class UserID(commands.UserConverter):
    """A conveter that takes the given value and tries to grab the ID from it
    Returns the ID of the user"""

    async def convert(self, ctx:commands.Context, value:str) -> int:
        """Converts the given value to a valid user ID"""

        # Maybe they gave a straight?
        try:
            return int(value)
        except ValueError:
            pass

        # They pinged the user
        match = self._get_id_match(value)
        if match is not None:
            return int(match.group(1))

        # Try and find their name from the user's relations
        ftm = FamilyTreeMember.get(ctx.author.id, ctx.family_guild_id)
        relations = ftm.get_direct_relations()
        if relations:
            redis_keys = [f"UserID-{i}" for i in relations]
            async with ctx.bot.redis() as re:
                usernames = await re.mget(*redis_keys)
            for uid, name in zip(relations, usernames):
                if name == value:
                    return uid

        # Ah well
        raise commands.BadArgument(f"User \"{value}\" not found")
