from discord.ext import commands
from discord.ext import tasks

from cogs.utils.custom_bot import CustomBot
from cogs.utils.custom_cog import Cog


class CommandEvent(Cog):
    """A cog for logging and handling the commands run"""

    def __init__(self, bot:CustomBot):
        super().__init__(bot, self.get_class_name('cog'))
        self.command_cache = []
        self.cache_logger.start()

    def cog_unload(self):
        """Stop the logger from running on cog unload"""

        self.cache_logger.stop()

    @Cog.listener()
    async def on_command_completion(self, ctx:commands.Context):
        """Add command to cog cache on completion"""

        self.command_cache.append(ctx)

    @Cog.listener()
    async def on_command_error(self, ctx:commands.Context, error):
        """Add command to cog cache on error"""

        self.command_cache.append(ctx)

    @Cog.listener()
    async def on_command(self, ctx:commands.Context):
        """Log command out to terminal when run"""

        cog = self.bot.get_cog(ctx.command.cog_name)
        if not cog:
            logger = self.log_handler
        else:
            logger = cog.log_handler 
        guild_id = ctx.guild.id or 'PMs'
        logger.debug(f"Command '{ctx.command.qualified_name}' run by {ctx.author.id} "
                      "on {guild_id}/{ctx.channel.id}")

    @tasks.loop(seconds=15)
    async def cache_logger(self):
        """Log and empty the cache of commands"""

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
        async with self.bot.database() as db:
            await db.conn.copy_records_to_table(
                'command_log',
                columns=['guild_id', 'channel_id', 'user_id', 'message_id', 'content', 
                         'command_name', 'invoked_with', 'command_prefix', 'timestamp', 
                         'command_failed', 'valid', 'shard_id'],
                records=command_values,
            )


def setup(bot:CustomBot):
    x = CommandEvent(bot)
    bot.add_cog(x)
