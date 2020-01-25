from discord.ext import tasks

from cogs import utils


class CommandEvent(utils.Cog):

    def __init__(self, bot:utils.Bot):
        super().__init__(bot)
        self.command_cache = []
        self.log_command_loop.start()

    def cog_unload(self):
        self.log_command_loop.stop()

    @utils.Cog.listener()
    async def on_command_completion(self, ctx:utils.Context):
        self.command_cache.append(ctx)

    @utils.Cog.listener()
    async def on_command_error(self, ctx:utils.Context, error):
        self.command_cache.append(ctx)

    @utils.Cog.listener()
    async def on_command(self, ctx:utils.Context):
        """Outputs command to debug log"""

        cog = self.bot.get_cog(ctx.command.cog_name)
        if not cog:
            logger = self.logger
        else:
            logger = cog.logger
        if ctx.guild:
            logger.debug(f"Command '{ctx.command.qualified_name}' run by {ctx.author.id} on {ctx.guild.id}/{ctx.channel.id}")
        else:
            logger.debug(f"Command '{ctx.command.qualified_name}' run by {ctx.author.id} on PMs/{ctx.channel.id}")

    @tasks.loop(seconds=15)
    async def log_command_loop(self):
        """Clears the command cache and stores everything in the database"""

        # Copy and clear caches
        commands = self.command_cache[:]
        self.command_cache.clear()

        # Log commands
        command_values = [[
            ctx.guild.id if ctx.guild else None,
            ctx.channel.id,
            ctx.author.id,
            ctx.message.id,
            ctx.message.content,
            ctx.command.name if ctx.command else None,
            ctx.invoked_with,
            ctx.prefix,
            ctx.message.created_at,
            ctx.command_failed,
            ctx.valid,
            ctx.guild.shard_id if ctx.guild else 0,
        ] for ctx in commands]

        # Save to DB
        columns = [
            'guild_id', 'channel_id', 'user_id', 'message_id', 'content', 'command_name',
            'invoked_with', 'command_prefix', 'timestamp', 'command_failed', 'valid', 'shard_id'
        ]
        async with self.bot.database() as db:
            await db.conn.copy_records_to_table(
                'command_log',
                columns=columns,
                records=command_values,
            )


def setup(bot:utils.Bot):
    x = CommandEvent(bot)
    bot.add_cog(x)
