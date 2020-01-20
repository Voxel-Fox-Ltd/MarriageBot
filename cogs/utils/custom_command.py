from discord.ext import commands


class CustomCommand(commands.Command):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, cooldown_after_parsing=kwargs.get('cooldown_after_parsing', True), **kwargs)
        self.ignore_checks_in_help = kwargs.get('ignore_checks_in_help', False)
        self.requires_set_config = kwargs.get('set_config', None)

    def get_set_config(self, ctx:commands.Context, *setting):
        config = ctx.bot.config
        for key in setting:
            config = config.get(key)
            if config is None or config == "":
                return commands.DisabledCommand()
        return True

    async def can_run(self, ctx:commands.Context):
        """The normal Command.can_run but it ignores cooldowns"""

        if self.ignore_checks_in_help:
            return True
        if self.requires_set_config:
            v = self.get_set_config(ctx, *self.requires_set_config)
            if v is False:
                raise commands.DisabledCommand()
        try:
            return await super().can_run(ctx)
        except commands.CommandOnCooldown:
            return True
        except commands.CommandError as e:
            raise e


class CustomGroup(commands.Group):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, cooldown_after_parsing=kwargs.get('cooldown_after_parsing', True), **kwargs)
        self.ignore_checks_in_help = kwargs.get('ignore_checks_in_help', False)
        self.requires_set_config = kwargs.get('set_config', None)

    def get_set_config(self, ctx:commands.Context, setting:list):
        config = ctx.bot.config
        for key in setting:
            config = config.get(key)
            if config is None or config == "":
                return commands.DisabledCommand()
        return True

    async def can_run(self, ctx:commands.Context):
        """The normal Command.can_run but it ignores cooldowns"""

        if self.ignore_checks_in_help:
            return True
        if self.requires_set_config:
            v = self.get_set_config(ctx, self.requires_set_config)
            if v is False:
                raise commands.DisabledCommand()
        try:
            return await super().can_run(ctx)
        except commands.CommandOnCooldown:
            return True
        except commands.CommandError as e:
            raise e
