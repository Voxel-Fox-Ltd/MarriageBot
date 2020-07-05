import asyncio
import collections
import glob
import logging
import typing
import copy
from datetime import datetime as dt
from urllib.parse import urlencode

import aiohttp
import discord
import toml
from discord.ext import commands

from cogs.utils.custom_context import CustomContext
from cogs.utils.database import DatabaseConnection
from cogs.utils.redis import RedisConnection


def get_prefix(bot, message:discord.Message):
    """Gives the prefix for the bot - override this to make guild-specific prefixes"""

    if message.guild is None:
        prefix = bot.config['default_prefix']
    else:
        prefix = bot.guild_settings[message.guild.id]['prefix'] or bot.config['default_prefix']
    if prefix in ["'", "‘"]:
        prefix = ["'", "‘"]
    prefix = [prefix] if isinstance(prefix, str) else prefix
    return commands.when_mentioned_or(*prefix)(bot, message)


class CustomBot(commands.AutoShardedBot):
    """A child of discord.ext.commands.AutoShardedBot to make things a little easier when
    doing my own stuff"""

    def __init__(self, config_file:str='config/config.toml', logger:logging.Logger=None, *args, **kwargs):
        """The initialiser for the bot object
        Note that we load the config before running the original method"""

        # Store the config file for later
        self.config = None
        self.config_file = config_file
        self.logger = logger or logging.getLogger("bot")
        self.reload_config()

        # Run original
        super().__init__(command_prefix=get_prefix, *args, **kwargs)

        # Set up our default guild settings
        self.DEFAULT_GUILD_SETTINGS = {
            'prefix': self.config['default_prefix'],
        }
        self.DEFAULT_USER_SETTINGS = {
        }

        # Aiohttp session
        self.session = aiohttp.ClientSession(loop=self.loop)

        # Allow database connections like this
        # if self.config['database'].get('enabled'):
        self.database = DatabaseConnection
        self.database.logger = self.logger.getChild('database')

        # Allow redis connections like this
        # if self.config['redis'].get('enabled'):
        self.redis = RedisConnection
        self.redis.logger = self.logger.getChild('redis')

        # Store the startup method so I can see if it completed successfully
        self.startup_time = dt.now()
        self.startup_method = None

        # Here's the storage for cached stuff
        self.guild_settings = collections.defaultdict(lambda: copy.deepcopy(self.DEFAULT_GUILD_SETTINGS))
        self.user_settings = collections.defaultdict(lambda: copy.deepcopy(self.DEFAULT_USER_SETTINGS))

    async def startup(self):
        """Clears all the bot's caches and fills them from a DB read"""

        # Remove caches
        self.logger.debug("Clearing caches")
        self.guild_settings.clear()
        self.user_settings.clear()

        # Get database connection
        db = await self.database.get_connection()

        # Get guild settings
        data = await self.get_all_table_data(db, "guild_settings")
        for row in data:
            for key, value in row.items():
                self.guild_settings[row['guild_id']][key] = value

        # Get user settings
        data = await self.get_all_table_data(db, "user_settings")
        for row in data:
            for key, value in row.items():
                self.user_settings[row['user_id']][key] = value

        # Wait for the bot to cache users before continuing
        self.logger.debug("Waiting until ready before completing startup method.")
        await self.wait_until_ready()

        # Close database connection
        await db.disconnect()

    async def run_sql_exit_on_error(self, db, sql, *args):
        """Get data form a table, exiting if it can't"""

        try:
            return await db(sql, *args)
        except Exception as e:
            self.logger.critical(f"Error selecting from table - {e}")
            exit(1)

    async def get_all_table_data(self, db, table_name):
        """Get all data from a table"""

        return await self.run_sql_exit_on_error(db, "SELECT * FROM {0}".format(table_name))

    async def get_list_table_data(self, db, table_name, key):
        """Get all data from a table"""

        return await self.run_sql_exit_on_error(db, "SELECT * FROM {0} WHERE key=$1".format(table_name), key)

    def get_invite_link(self, *, scope:str='bot', response_type:str=None, redirect_uri:str=None, guild_id:int=None, **kwargs):
        """Gets the invite link for the bot, with permissions all set properly"""

        permissions = discord.Permissions()
        for name, value in kwargs.items():
            setattr(permissions, name, value)
        data = {
            'client_id': self.config.get('oauth', {}).get('client_id', None) or self.user.id,
            'scope': scope,
            'permissions': permissions.value
        }
        if redirect_uri:
            data['redirect_uri'] = redirect_uri
        if guild_id:
            data['guild_id'] = guild_id
        if response_type:
            data['response_type'] = response_type
        return 'https://discordapp.com/oauth2/authorize?' + urlencode(data)

    async def add_delete_button(self, message:discord.Message, valid_users:typing.List[discord.User], *, delete:typing.List[discord.Message]=None, timeout=60.0):
        """Adds a delete button to the given message"""

        # Let's not add delete buttons to DMs
        if isinstance(message.channel, discord.DMChannel):
            return

        # Add reaction
        await message.add_reaction("\N{WASTEBASKET}")

        # Fix up arguments
        if not isinstance(valid_users, list):
            valid_users = [valid_users]

        # Wait for response
        def check(r, u) -> bool:
            if r.message.id != message.id:
                return False
            if u.bot is True:
                return False
            if isinstance(u, discord.Member) is False:
                return False
            if getattr(u, 'roles', None) is None:
                return False
            if str(r.emoji) != "\N{WASTEBASKET}":
                return False
            if u.id in [user.id for user in valid_users] or u.permissions_in(message.channel).manage_messages:
                return True
            return False
        try:
            await self.wait_for("reaction_add", check=check, timeout=timeout)
        except asyncio.TimeoutError:
            try:
                return await message.remove_reaction("\N{WASTEBASKET}", self.user)
            except Exception:
                return

        # We got a response
        if delete is None:
            delete = [message]

        # Try and bulk delete
        bulk = False
        if message.guild:
            permissions: discord.Permissions = message.channel.permissions_for(message.guild.me)
            bulk = permissions.manage_messages and permissions.read_message_history
        try:
            await message.channel.purge(check=lambda m: m.id in [i.id for i in delete], bulk=bulk)
        except Exception:
            return  # Ah well

    @property
    def owner_ids(self) -> list:
        """Gives you a list of the owner IDs"""

        return self.config['owners']

    @owner_ids.setter
    def owner_ids(self, value):
        """A setter method so that the original bot object doesn't complain"""

        pass

    def get_uptime(self) -> float:
        """Gets the uptime of the bot in seconds
        Uptime is a bit of a misnomer, since it starts when the instance is created, but
        yknow that's close enough"""

        return (dt.now() - self.startup_time).total_seconds()

    async def get_context(self, message, *, cls=CustomContext):
        """Gently insert a new original_author field into the context"""

        ctx = await super().get_context(message, cls=cls)
        ctx.original_author_id = ctx.author.id
        return ctx

    def get_extensions(self) -> list:
        """Gets a list of filenames of all the loadable cogs"""

        ext = glob.glob('cogs/[!_]*.py')
        extensions = [i.replace('\\', '.').replace('/', '.')[:-3] for i in ext]
        self.logger.debug("Getting all extensions: " + str(extensions))
        return extensions

    def load_all_extensions(self):
        """Loads all the given extensions from self.get_extensions()"""

        # Unload all the given extensions
        self.logger.info('Unloading extensions... ')
        for i in self.get_extensions():
            try:
                self.unload_extension(i)
            except Exception as e:
                self.logger.debug(f' * {i}... failed - {e!s}')
            else:
                self.logger.info(f' * {i}... success')

        # Now load em up again
        self.logger.info('Loading extensions... ')
        for i in self.get_extensions():
            try:
                self.load_extension(i)
            except Exception as e:
                self.logger.critical(f' * {i}... failed - {e!s}')
                raise e
            else:
                self.logger.info(f' * {i}... success')

    async def set_default_presence(self, shard_id:int=None):
        """Sets the default presence for the bot as appears in the config file"""

        # Update presence
        self.logger.info("Setting default bot presence")
        presence = self.config['presence']  # Get text

        # Update per shard
        if self.shard_count > 1:

            # Get shard IDs
            if shard_id:
                min, max = shard_id, shard_id + 1  # If we're only setting it for one shard
            else:
                min, max = self.shard_ids[0], self.shard_ids[-1]  # If we're setting for all shards

            # Go through each shard ID
            for i in range(min, max):
                activity = discord.Activity(
                    name=f"{presence['text']} (shard {i})",
                    type=getattr(discord.ActivityType, presence['activity_type'].lower())
                )
                status = getattr(discord.Status, presence['status'].lower())
                await self.change_presence(activity=activity, status=status, shard_id=i)

        # Not sharded - just do everywhere
        else:
            activity = discord.Activity(
                name=presence['text'],
                type=getattr(discord.ActivityType, presence['activity_type'].lower())
            )
            status = getattr(discord.Status, presence['status'].lower())
            await self.change_presence(activity=activity, status=status)

    def reload_config(self):
        """Re-reads the config file into cache"""

        self.logger.info("Reloading config")
        try:
            with open(self.config_file) as a:
                self.config = toml.load(a)
        except Exception as e:
            self.logger.critical(f"Couldn't read config file - {e}")
            exit(1)

    async def login(self, token:str=None, *args, **kwargs):
        """The original login method with optional token"""

        await super().login(token or self.config['token'], *args, **kwargs)

    async def start(self, token:str=None, *args, **kwargs):
        """Start the bot with the given token, create the startup method task"""

        if self.config['database']['enabled']:
            self.logger.info("Running startup method")
            self.startup_method = self.loop.create_task(self.startup())
        else:
            self.logger.info("Not running bot startup method due to database being disabled")
        self.logger.info("Running original D.py start method")
        await super().start(token or self.config['token'], *args, **kwargs)

    async def close(self, *args, **kwargs):
        """The original bot close method, but with the addition of closing the
        aiohttp ClientSession that was opened on bot creation"""

        self.logger.debug("Closing aiohttp ClientSession")
        await asyncio.wait_for(self.session.close(), timeout=None)
        self.logger.debug("Running original D.py logout method")
        await super().close(*args, **kwargs)
