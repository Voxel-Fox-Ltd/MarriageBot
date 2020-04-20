from cogs import utils


class NameHandler(utils.Cog):

    @utils.Cog.listener()
    async def on_command(self, ctx:utils.Context):
        """Caches a user's name when they run any command"""

        await self.bot.get_name(ctx.author.id, fetch_from_api=True)


def setup(bot:utils.Bot):
    x = NameHandler(bot)
    bot.add_cog(x)
