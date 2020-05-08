from cogs import utils


class NameHandler(utils.Cog):

    @utils.Cog.listener()
    async def on_command(self, ctx:utils.Context):
        """Caches a user's name when they run any command"""

        user = self.bot.shallow_users.get(ctx.author.id)
        if user is None:
            # user = utils.ShallowUser(ctx.author.id)
            # self.bot.shallow_users[ctx.author.id] = user
            return
        user.age += 1
        if user.age >= utils.ShallowUser.LIFETIME_THRESHOLD:
            await self.bot.get_name(ctx.author.id, fetch_from_api=True)


def setup(bot:utils.Bot):
    x = NameHandler(bot)
    bot.add_cog(x)
