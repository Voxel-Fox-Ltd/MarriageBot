from discord.ext import commands


class ConfigNotSet(commands.DisabledCommand):
    """A failure for the config not being set"""

    pass


def is_config_set(*config_keys):
    """Checks that your config has been set given the keys for the item"""

    def predicate(ctx:commands.Context):
        working_config = ctx.bot.config
        try:
            for key in config_keys:
                working_config = working_config[key]
        except KeyError:
            raise ConfigNotSet()
        if working_config in [None, ""]:
            ctx.bot.logger.warning(f"No config is set for {'.'.join(config_keys)}")
            raise ConfigNotSet
        return True
    return predicate
