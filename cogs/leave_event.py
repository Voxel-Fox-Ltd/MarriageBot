from discord import Member
from discord.ext.commands import Cog

from cogs.utils.custom_bot import CustomBot
from cogs.utils.family_tree.family_tree_member import FamilyTreeMember


class LeaveEvent(Cog):

    def __init__(self, bot:CustomBot):
        self.bot = bot 


    @Cog.listener()
    async def on_member_remove(self, member:Member):
        '''
        Checks if you have the member stored, and if not, then removes them from 
        cache and database
        '''

        if self.bot.get_user(member.id) == None:
            ftm = FamilyTreeMember.get(member.id)
            if not ftm.is_empty():
                async with self.bot.database() as db:
                    await db.destroy(member.id)
            ftm.destroy()


def setup(bot:CustomBot):
    x = LeaveEvent(bot)
    bot.add_cog(x)
