from discord.ext import commands


class CantSendFiles(commands.CheckFailure):
    """The generic failure for not being able to send a file"""

    pass


def can_send_files():
    """The check for being able to send files into the channel"""

    async def predicate(ctx:commands.Context):
        if ctx.guild is None:
            return True
        if ctx.guild.me.permissions_in(ctx.channel).attach_files:
            return True
        raise CantSendFiles()
    return commands.check(predicate)
