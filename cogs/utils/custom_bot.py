from datetime import datetime as dt
import toml
import glob
import logging
from urllib.parse import urlencode
import os
import asyncio
import collections
import typing

import aiohttp
import discord
from discord.ext import commands

from cogs.utils.database import DatabaseConnection
from cogs.utils.custom_context import CustomContext


def get_prefix(bot, message:discord.Message):
    """Gives the prefix for the bot - override this to make guild-specific prefixes"""

    if message.guild is None:
        return commands.when_mentioned_or(bot.config['default_prefix'])(bot, message)
    prefix = bot.guild_settings[message.guild.id]['prefix'] or bot.config['default_prefix']
    return commands.when_mentioned_or(prefix)(bot, message)


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

        # Aiohttp session
        self.session = aiohttp.ClientSession(loop=self.loop)

        # Allow database connections like this
        self.database = DatabaseConnection
        self.database.logger = self.logger.getChild('database')

        # Store the startup method so I can see if it completed successfully
        self.startup_time = dt.now()
        self.startup_method = None

        # Here's the storage for cached stuff
        self.guild_settings = collections.defaultdict(self.DEFAULT_GUILD_SETTINGS.copy)

    def get_invite_link(self, *, join_server_redirect_uri:str=None, guild_id:int=None, **kwargs):
        """Gets the invite link for the bot, with permissions all set properly"""

        permissions = discord.Permissions()
        for name, value in kwargs.items():
            setattr(permissions, name, value)
        data = {
            'client_id': self.config.get('oauth', {}).get('client_id', None) or self.user.id,
            'scope': 'bot',
            'permissions': permissions.value
        }
        if join_server_redirect_uri:
            data['redirect_uri'] = join_server_redirect_uri
        if guild_id:
            data['guild_id'] = guild_id
        return 'https://discordapp.com/oauth2/authorize?' + urlencode(data)

    async def add_delete_button(self, message:discord.Message, valid_users:typing.List[discord.User], *, timeout=60.0):
        """Adds a delete button to the given message"""

        # Add reaction
        await message.add_reaction("\N{WASTEBASKET}")

        # Wait for response
        check = lambda r, u: all([
            r.message.id == message.id,
            u.id in [user.id for user in valid_users],
            str(r.emoji) == "\N{WASTEBASKET}"
        ])
        try:
            await self.wait_for("reaction_add", check=check, timeout=timeout)
        except asyncio.TimeoutError:
            try:
                return await message.remove_reaction("\N{WASTEBASKET}", self.user)
            except Exception:
                return

        # We got a response
        try:
            await message.delete()
        except (discord.Forbidden, discord.NotFound):
            return  # Ah well

    @property
    def owner_ids(self) -> list:
        """Gives you a list of the owner IDs"""

        return self.config['owners']

    @owner_ids.setter
    def owner_ids(self, value):
        """A setter method so that the original bot object doesn't complain"""

        pass

    async def startup(self):
        """Clears all the bot's caches and fills them from a DB read"""

        # Remove caches
        self.logger.debug("Clearing caches")
        self.guild_settings.clear()

        # Get database connection
        db = await self.database.get_connection()

        # Get stored prefixes
        try:
            guild_data = await db("SELECT * FROM guild_settings")
        except Exception as e:
            self.logger.critical(f"Error selecting from guild_settings - {e}")
            exit(1)
        for row in guild_data:
            self.guild_settings[row['guild_id']] = dict(row)

        # Wait for the bot to cache users before continuing
        self.logger.debug("Waiting until ready before completing startup method.")
        await self.wait_until_ready()

        # Close database connection
        await db.disconnect()

    def get_uptime(self) -> float:
        """Gets the uptime of the bot in seconds
        Uptime is a bit of a misnomer, since it starts when the instance is created, but
        yknow that's close enough"""

        return (dt.now() - self.startup_time).total_seconds()

    async def get_context(self, message, *, cls=commands.Context):
        """Gently insert a new original_author field into the context"""

        ctx = await super().get_context(message, cls=CustomContext)
        if ctx.guild:
            ctx.original_author = ctx.guild.get_member(message.author.id)
        else:
            ctx.original_author = self.get_user(message.author.id)
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
                self.logger.warning(f' * {i}... failed - {e!s}')
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

    async def set_default_presence(self):
        """Sets the default presence for the bot as appears in the config file"""

        # Update presence
        self.logger.info("Setting default bot presence")
        presence = self.config['presence']
        if self.shard_count > 1:
            for i in range(self.shard_count):
                activity = discord.Activity(
                    name=f"{presence['text']} (shard {i})",
                    type=getattr(discord.ActivityType, presence['activity_type'].lower())
                )
                status = getattr(discord.Status, presence['status'].lower())
                await self.change_presence(activity=activity, status=status, shard_id=i)
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
            self.logger.critical("Couldn't read config file")
            raise e

    async def login(self, token:str=None, *args, **kwargs):
        """The original login method with optional token"""

        await super().login(token or self.config['token'], *args, **kwargs)

    async def start(self, token:str=None, *args, **kwargs):
        """Start the bot with the given token, create the startup method task"""

        self.logger.info("Running startup method")
        self.startup_method = self.loop.create_task(self.startup())
        self.logger.info("Running original D.py start method")
        await super().start(token or self.config['token'], *args, **kwargs)

    async def close(self, *args, **kwargs):
        """The original bot close method, but with the addition of closing the
        aiohttp ClientSession that was opened on bot creation"""

        self.logger.debug("Closing aiohttp ClientSession")
        await asyncio.wait_for(self.session.close(), timeout=None)
        self.logger.debug("Running original D.py logout method")
        await super().close(*args, **kwargs)
