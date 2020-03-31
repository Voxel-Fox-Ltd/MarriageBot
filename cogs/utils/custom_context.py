from discord.ext import commands


class CustomContext(commands.Context):

    async def okay(self):
        """Adds the okay hand reaction to a message"""

        return await self.message.add_reaction("\N{OK HAND SIGN}")

    async def send(self, *args, ignore_error:bool=False, **kwargs):
        """The normal ctx.send but with an optional arg to ignore errors"""

        try:
            return await super().send(*args, **kwargs)
        except Exception as e:
            if ignore_error:
                return None
            raise e
