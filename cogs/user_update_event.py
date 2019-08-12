import discord

from cogs.utils.custom_bot import CustomBot
from cogs.utils.custom_cog import Cog 


class UserUpdateEvent(Cog):

    def __init__(self, bot:CustomBot):
        self.bot = bot
        super().__init__(__class__.__name__)

    @Cog.listener()
    async def on_user_update(self, before:discord.User, after:discord.User):
        """Recaches a username change"""

        if before.name == after.name:
            return 
        async with self.bot.redis() as re:
            await re.set(f'UserName-{after.id}', str(after))


def setup(bot:CustomBot):
    x = UserUpdateEvent(bot)
    bot.add_cog(x)
