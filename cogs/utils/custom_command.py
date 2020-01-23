from discord.ext import commands


class CustomCommand(commands.Command):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, cooldown_after_parsing=kwargs.get('cooldown_after_parsing', True), **kwargs)
        self.ignore_checks_in_help = kwargs.get('ignore_checks_in_help', False)

    async def can_run(self, ctx:commands.Context):
        """The normal Command.can_run but it ignores cooldowns"""

        if self.ignore_checks_in_help:
            return True
        return await super().can_run(ctx)
        # try:
        #     return await super().can_run(ctx)
        # except commands.CommandOnCooldown:
        #     return True
        # except commands.CommandError as e:
        #     raise e

    def _prepare_cooldowns(self, ctx:commands.Context):
        """Prepares all the cooldowns for the command to be called"""

        try:
            super()._prepare_cooldowns(ctx)
        except commands.CommandOnCooldown as e:
            raise getattr(e.cooldown, error(e.cooldown, e.retry_after), e)


class CustomGroup(commands.Group):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, cooldown_after_parsing=kwargs.get('cooldown_after_parsing', True), **kwargs)
        self.ignore_checks_in_help = kwargs.get('ignore_checks_in_help', False)

    async def can_run(self, ctx:commands.Context):
        """The normal Command.can_run but it ignores cooldowns"""

        if self.ignore_checks_in_help:
            return True
        try:
            return await super().can_run(ctx)
        except commands.CommandOnCooldown:
            return True
        except commands.CommandError as e:
            raise e
