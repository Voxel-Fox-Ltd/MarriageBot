from discord.ext import commands


class NoSetConfig(commands.CommandError):
    """Thrown when there's a missing item in the config"""

    def __init__(self, args):
        self.items: list = args


def has_set_config(*args):
    """The check to make sure that the bot's config has a given item set
    eg, @has_set_config("a", "b") would look for bot.config['a']['b']"""

    async def predicate(ctx:commands.Context):
        data = ctx.bot.config
        for i in args:
            try:
                data = data[i]
            except (KeyError, IndexError):
                raise NoSetConfig(args)
        return True
    return commands.check(predicate)
