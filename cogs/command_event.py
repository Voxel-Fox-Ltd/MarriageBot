from asyncio import sleep

from discord import Message, Embed
from discord.ext.commands import Context

from cogs.utils.custom_bot import CustomBot


class CommandEvent(object):

    def __init__(self, bot:CustomBot):
        self.bot = bot
        self.logger = self.bot.loop.create_task(self.run_logger())

        self.command_cache = []


    async def on_command(self, ctx:Context):
        self.command_cache.append(ctx)


    async def run_logger(self):
        '''
        Opens a database connection
        '''

        await self.bot.wait_until_ready()
        while not self.bot.is_closed():

            # Wait a lil bit
            await sleep(15)

            # Copy and clear caches
            commands = self.command_cache[:]
            self.command_cache.clear()
                
            # Log commands
            command_sql = '''INSERT INTO command_log
                    (guild_id, channel_id, user_id, message_id, content, command_name, invoked_with, command_prefix, timestamp)
                    VALUES
                    ($1, $2, $3, $4, $5, $6, $7, $8, $9)'''
            command_values = [[
                    ctx.guild.id if ctx.guild else None,
                    ctx.channel.id, 
                    ctx.author.id, 
                    ctx.message.id,
                    ctx.message.content, 
                    ctx.command.name, 
                    ctx.invoked_with,
                    ctx.prefix,
                    ctx.message.created_at,
            ] for ctx in commands]

            # Save to DB
            async with self.bot.database() as db:
                await db.conn.copy_records_to_table(
                    'command_log',
                    columns=['guild_id', 'channel_id', 'user_id', 'message_id', 'content', 'command_name', 'invoked_with', 'command_prefix', 'timestamp'],
                    records=command_values,
                )


def setup(bot:CustomBot):
    x = CommandEvent(bot)
    bot.add_cog(x)
