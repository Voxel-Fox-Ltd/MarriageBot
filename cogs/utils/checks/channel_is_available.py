from discord.ext.commands import check, Context, CheckFailure


class ChannelNotAvailable(CheckFailure):
    def __init__(self, message: str = None):
        self.message = message


def channel_is_available():
    """Returns True if the channel is available for the bot to talk in"""

    def predicate(ctx: Context):
        bot = ctx.bot
        if ctx.channel.id in bot.blacklisted_channels.get(ctx.guild.id, list()):
            # raise ChannelNotAvailable(bot.channel_blacklist_message.get(ctx.guild.id))
            raise ChannelNotAvailable()
        return True

    return check(predicate)
