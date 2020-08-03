from cogs import utils


class CommandEvent(utils.Cog):

    CONTENT_LIMIT = 50

    @utils.Cog.listener()
    async def on_command(self, ctx:utils.Context):
        """Pinged when a command is invoked"""

        if ctx.command is None:
            return
        logger = ctx.cog.logger if ctx.cog else self.logger
        content = ctx.message.content.replace('\n', '\\n')[:self.CONTENT_LIMIT]
        if len(ctx.message.content) > self.CONTENT_LIMIT:
            content += '...'
        if ctx.guild is None:
            return logger.info(f"Command invoked ({ctx.invoked_with}) ~ (G0/C{ctx.channel.id}/U{ctx.author.id}) :: {content}")
        logger.info(f"Command invoked ({ctx.invoked_with}) ~ (G{ctx.guild.id}/C{ctx.channel.id}/U{ctx.author.id}) :: {content}")


def setup(bot:utils.Bot):
    x = CommandEvent(bot)
    bot.add_cog(x)
