import datetime

from discord.ext import commands


class CustomCommand(commands.Command):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, cooldown_after_parsing=kwargs.get('cooldown_after_parsing', True), **kwargs)
        self.ignore_checks_in_help = kwargs.get('ignore_checks_in_help', False)
        mapping = getattr(self._buckets._cooldown.__class__, 'mapping', None)
        if mapping:
            self._buckets = self._buckets._cooldown.__class__.mapping(self._buckets._cooldown)

    async def can_run(self, ctx:commands.Context):
        """The normal Command.can_run but it ignores cooldowns"""

        if self.ignore_checks_in_help:
            return True
        return await super().can_run(ctx)

    def _prepare_cooldowns(self, ctx:commands.Context):
        """Prepares all the cooldowns for the command to be called"""

        if self._buckets.valid:
            current = ctx.message.created_at.replace(tzinfo=datetime.timezone.utc).timestamp()
            bucket = self._buckets.get_bucket(ctx.message, current)
            try:
                if bucket.predicate(ctx.message) is False:
                    return
            except AttributeError:
                ctx.bot.logger.critical(f"Invalid cooldown set on command {ctx.invoked_with}")
                raise commands.CheckFailure("Invalid cooldown set for this command")
            retry_after = bucket.update_rate_limit(current)
            if retry_after:
                try:
                    error = bucket.error
                except AttributeError:
                    error = bucket.default_cooldown_error
                raise error(bucket, retry_after)


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
