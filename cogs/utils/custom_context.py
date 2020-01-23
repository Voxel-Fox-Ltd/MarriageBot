from discord.ext import commands


class CustomContext(commands.Context):

    async def okay(self):
        """Adds the okay hand reaction to a message"""

        return await self.message.add_reaction("\N{OK HAND SIGN}")
