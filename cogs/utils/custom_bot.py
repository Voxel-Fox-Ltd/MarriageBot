from datetime import datetime as dt
import toml
import glob
import logging
from urllib.parse import urlencode
import os

import aiohttp
import discord
from discord.ext import commands

from cogs.utils.database import DatabaseConnection


def get_prefix(bot, message:discord.Message):
    """Gives the prefix for the bot - override this to make guild-specific prefixes"""

    return commands.when_mentioned_or(bot.config['default_prefix'])(bot, message)


class CustomBot(commands.AutoShardedBot):
    """A child of discord.ext.commands.AutoShardedBot to make things a little easier when
    doing my own stuff"""

    def __init__(self, config_file:str='config/config.toml', commandline_args=None, logger:logging.Logger=None, *args, **kwargs):
        super().__init__(command_prefix=get_prefix, *args, **kwargs)

        # Store the config file for later
        self.config = None
        self.config_file = config_file
        self.logger = logger or logging.getLogger(os.getcwd().split(os.sep)[-1]).getChild("bot")
        self.reload_config()
        self.commandline_args = commandline_args
        self._invite_link = None

        # Aiohttp session
        self.session = aiohttp.ClientSession(loop=self.loop)

        # Allow database connections like this
        self.database = DatabaseConnection
        self.database.logger = self.logger.getChild('database')

        # Store the startup method so I can see if it completed successfully
        self.startup_time = dt.now()
        self.startup_method = None

    @property
    def invite_link(self):
        """Gets the invite link for the bot, with permissions all set properly"""

        # https://discordapp.com/oauth2/authorize?client_id=468281173072805889&scope=bot&permissions=35840&guild_id=208895639164026880
        if self._invite_link: 
            return self._invite_link
        permissions = discord.Permissions()
        permissions.read_messages = True 
        permissions.send_messages = True 
        permissions.embed_links = True 
        permissions.attach_files = True 
        self._invite_link = 'https://discordapp.com/oauth2/authorize?' + urlencode({
            'client_id': self.user.id,
            'scope': 'bot',
            'permissions': permissions.value
        })
        return self.invite_link

    async def startup(self):
        """Clears all the bot's caches and fills them from a DB read"""

        # Remove caches
        self.logger.debug("Clearing caches")

        # Get database connection
        db = await self.database.get_connection()

        # Wait for the bot to cache users before continuing
        self.logger.debug("Waiting until ready before completing startup method.")
        await self.wait_until_ready() 

        # Close database connection
        await db.disconnect()
        
        
    # async def on_message(self, message:discord.Message):
    #     """Invokes the command with a custom context"""

    #     ctx = await self.get_context(message)
    #     await self.invoke(ctx)


    def get_uptime(self) -> float:
        """Gets the uptime of the bot in seconds
        Uptime is a bit of a misnomer, since it starts when the instance is created, but
        yknow that's close enough"""

        return (dt.now() - self.startup_time).total_seconds()


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
            self.logger.info(f' * {i}... success')

        # Now load em up again
        self.logger.info('Loading extensions... ')
        for i in self.get_extensions():
            try:
                self.load_extension(i)
            except Exception as e:
                self.logger.error(f' * {i}... failed - {e!s}')
                raise e
            self.logger.info(f' * {i}... success')

    async def set_default_presence(self):
        """Sets the default presence for the bot as appears in the config file"""
        
        # Update presence
        self.logger.info("Setting default bot presence")
        presence_text = self.config['presence_text']
        if self.shard_count > 1:
            for i in range(self.shard_count):
                game = discord.Game(f"{presence_text} (shard {i})")
                await self.change_presence(activity=game, shard_id=i)
        else:
            game = discord.Game(presence_text)
            await self.change_presence(activity=game)

    def reload_config(self):
        """Re-reads the config file into cache"""

        self.logger.info("Reloading config")
        try:
            with open(self.config_file) as a:
                self.config = toml.load(a)
        except Exception as e:
            self.logger.critical("Couldn't read config file")
            raise e

    def run(self):
        """Runs the bot wew"""

        super().run(self.config['token'])

    async def start(self, token:str=None):
        """Start the bot with the given token, create the startup method task"""

        self.logger.info("Running startup method") 
        self.startup_method = self.loop.create_task(self.startup())
        self.logger.info("Running original D.py start method")
        await super().start(token or self.config['token'])

    async def logout(self):
        """Log out the bot and kill all of its running processes"""

        self.logger.info("Closing aiohttp ClientSession")
        await self.session.close()
        self.logger.info("Running original D.py logout method")
        await super().logout()
