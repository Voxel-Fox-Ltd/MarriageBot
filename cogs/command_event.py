from asyncio import sleep

from discord import Message, Embed
from discord.ext.commands import Context

from cogs.utils.custom_bot import CustomBot
from cogs.utils.custom_cog import Cog


class CommandEvent(Cog):

    def __init__(self, bot:CustomBot):
        super().__init__(self.__class__.__name__)
        self.bot = bot
        self.logger = self.bot.loop.create_task(self.run_logger())
        self.command_cache = []


    def cog_unload(self):
        self.logger.cancel()
        self.bot.loop.run_until_complete(self.empty_cache())


    @Cog.listener()
    async def on_command_completion(self, ctx:Context):
        self.command_cache.append(ctx)


    @Cog.listener()
    async def on_command_error(self, ctx:Context, error):
        self.command_cache.append(ctx)


    @Cog.listener()
    async def on_command(self, ctx:Context):
        '''Outputs command to debug log'''

        cog = self.bot.get_cog(ctx.command.cog_name)
        if not cog:
            logger = self.log_handler
        else:
            logger = cog.log_handler 
        if ctx.guild:
            logger.debug(f"Command '{ctx.command.qualified_name}' run by {ctx.author.id} on {ctx.guild.id}/{ctx.channel.id}")
        else:
            logger.debug(f"Command '{ctx.command.qualified_name}' run by {ctx.author.id} on PMs/{ctx.channel.id}")


    async def run_logger(self):
        '''
        Runs the logger loop that stores the commands
        '''

        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            await sleep(15)
            await self.log_cache()


    async def log_cache(self):
        '''
        Clears the command cache and stores everything in the database
        '''

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
                columns=['guild_id', 'channel_id', 'user_id', 'message_id', 'content', 'command_name', 'invoked_with', 'command_prefix', 'timestamp', 'command_failed', 'valid', 'shard_id'],
                records=command_values,
            )


def setup(bot:CustomBot):
    x = CommandEvent(bot)
    bot.add_cog(x)
