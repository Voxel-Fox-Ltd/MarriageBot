from datetime import datetime as dt
from asyncio import TimeoutError as AsyncioTimeoutError, wait_for
from glob import glob
import re as regex
import logging
from urllib.parse import urlencode
import collections
import typing

import aiohttp
import discord
from discord.ext.commands import AutoShardedBot, when_mentioned_or
import toml
import ujson as json

from cogs.utils.database import DatabaseConnection
from cogs.utils.redis import RedisConnection
from cogs.utils.family_tree.family_tree_member import FamilyTreeMember
from cogs.utils.customised_tree_user import CustomisedTreeUser
from cogs.utils.proposal_cache import ProposalCache
from cogs.utils.custom_context import CustomContext


def get_prefix(bot, message:discord.Message):
    """Gives the prefix for the bot for a given guild"""

    # Try and get their guild settings from the bot
    try:
        x = bot.guild_settings.get(
            message.guild.id,
            {'prefix': bot.config['prefix']['default_prefix']}
        )['prefix']
    # No prefix? No problem use the default
    except AttributeError:
        x = bot.config['prefix']['default_prefix']

    # If we don't respect custom prefixes, go back to the default
    if not bot.config['prefix']['respect_custom']:
        x = bot.config['prefix']['default_prefix']

    # Allow mentions
    return when_mentioned_or(x)(bot, message)


class CustomBot(AutoShardedBot):
    """A fancy-ass verison of the normal AutoShardedBot
    I've stuck a bunch of stuff inside it so it's easier for me to use
    for my stuff, but ultimately it's the same ol' AutoShardedBot that the
    library provides to start with"""

    def __init__(self, *args, config_file:str='config/config.json',
                 logger:logging.Logger=logging.getLogger(), **kwargs):
        # Let Danny handle most of it
        super().__init__(command_prefix=get_prefix, *args, **kwargs)

        # Throw down the root logger
        self.logger: logging.Logger = logger

        # Have somewhere to store the config
        self.config: dict = None
        self.config_file: str = config_file
        self.reload_config()

        # Set up arguments that are used in cogs and stuff
        self.bad_argument = regex.compile(r'(User|Member) "(.*)" not found')
        self._invite_link = None  # populated by 'invite' command
        self.support_guild = None  # populated by Patreon or bot mod check

        # Set up stuff that'll be used bot-wide
        self.shallow_users: typing.Dict[int, typing.Tuple[str, int]] = {}
        self.session = aiohttp.ClientSession(loop=self.loop)  # Session for DBL post
        self.startup_time = dt.now()
        self.startup_method = None
        self.deletion_method = None

        # Set up stuff that'll be used literally everywhere
        self.database = DatabaseConnection
        DatabaseConnection.logger = self.logger.getChild("database")
        self.redis = RedisConnection
        RedisConnection.logger = self.logger.getChild("redis")

        # Set up some caches
        self.server_specific_families: typing.List[int] = []  # List of whitelisted guild IDs
        self.proposal_cache: typing.Dict[int, tuple] = ProposalCache()
        self.blacklisted_guilds: typing.List[int] = []
        self.blocked_users: typing.List[int, typing.List[int]] = collections.defaultdict(list)
        self.guild_settings: typing.Dict[int, dict] = {}
        self.dbl_votes: typing.Dict[int, dt] = {}

        # Put the bot object in some other classes
        FamilyTreeMember.bot = self
        CustomisedTreeUser.bot = self
        ProposalCache.bot = self

    @property
    def invite_link(self):
        """The invite link for the bot, with all permissions in tow"""

        if self._invite_link:
            return self._invite_link
        permissions = discord.Permissions()
        permissions.read_messages = True
        permissions.send_messages = True
        permissions.embed_links = True
        permissions.attach_files = True
        self._invite_link = 'https://discordapp.com/oauth2/authorize?' + urlencode({
            'client_id': self.config['oauth']['client_id'],
            'scope': 'bot',
            'permissions': permissions.value
        })
        return self._invite_link

    def invite_link_to_guild(self, guild_id:int):
        """Returns an invite link to a guild

        Params:
            guild_id: int
                The ID for the guild the invite link should default to
        """

        return self.invite_link + f'&guild_id={guild_id}'

    @property
    def is_server_specific(self) -> bool:
        """Whether or not the bot is running the server specific version"""

        return self.config['server_specific']

    def allows_incest(self, guild_id:int) -> bool:
        """Returns if a given guild allows incest or not

        Params:
            guild_id: int
                The ID for the guild you want to check against
        """

        return self.is_server_specific and guild_id in self.guild_settings and self.guild_settings[guild_id]['allow_incest']

    async def startup(self):
        """The startup method for the bot - clears all the caches and reads
        everything out again from the database, essentially starting anew
        as if rebooted"""

        # Remove caches
        self.logger.debug("Clearing caches")
        FamilyTreeMember.all_users.clear()
        CustomisedTreeUser.all_users.clear()
        self.blacklisted_guilds.clear()
        self.guild_settings.clear()
        self.dbl_votes.clear()
        self.blocked_users.clear()

        # Grab a database connection
        db: DatabaseConnection = await self.database.get_connection()

        # Pick up the blacklisted guilds from the db
        try:
            blacklisted = await db('SELECT * FROM blacklisted_guilds')
        except Exception as e:
            self.logger.critical("Ran into an erorr selecting blacklisted guilds")
            raise e
        self.logger.debug(f"Caching {len(blacklisted)} blacklisted guilds")
        self.blacklisted_guilds = [i['guild_id'] for i in blacklisted]

        # Pick up the blocked users
        try:
            blocked = await db('SELECT * FROM blocked_user')
        except Exception as e:
            self.logger.critical("Ran into an error selecting blocked users")
            raise e
        self.logger.debug(f"Caching {len(blocked)} blocked users")
        for user in blocked:
            self.blocked_users[user['user_id']].append(user['blocked_user_id'])

        # Grab the command prefixes per guild
        try:
            settings = await db('SELECT * FROM guild_settings')
        except Exception as e:
            self.logger.critical("Ran into an error selecting guild settings")
            raise e
        self.logger.debug(f"Caching {len(settings)} guild settings")
        for guild_setting in settings:
            self.guild_settings[guild_setting['guild_id']] = dict(guild_setting)

        # Grab the last vote times of each user
        try:
            votes = await db('SELECT * FROM dbl_votes')
        except Exception as e:
            self.logger.critical("Ran into an error selecting DBL votes")
            raise e
        self.logger.debug(f"Caching {len(votes)} DBL votes")
        for v in votes:
            self.dbl_votes[v['user_id']] = v['timestamp']

        # Wait for the bot to cache users before continuing
        self.logger.debug("Waiting until ready before completing startup method.")
        await self.wait_until_ready()

        # Look through and find what servers the bot is allowed to be on, if server specific
        if self.is_server_specific:
            try:
                allowed_guilds = await db('SELECT guild_id FROM guild_specific_families')
            except Exception as e:
                self.logger.critical("Ran into an error selecting server specific guilds")
                raise e
            allowed_guild_ids = [i['guild_id'] for i in allowed_guilds]
            current_guild_ids = self._connection._guilds.keys()
            guild_ids_to_leave = [i for i in current_guild_ids if i not in allowed_guild_ids]
            for guild_id in guild_ids_to_leave:
                guild = self.get_guild(guild_id)
                await guild.leave()

        # Get family data from database
        try:
            if self.is_server_specific:
                partnerships = await db('SELECT * FROM marriages WHERE guild_id<>0')
                parents = await db('SELECT * FROM parents WHERE guild_id<>0')
            else:
                partnerships = await db('SELECT * FROM marriages WHERE guild_id=0')
                parents = await db('SELECT * FROM parents WHERE guild_id=0')
        except Exception as e:
            self.logger.critical("Ran into an error selecting either marriages or parents")
            raise e

        # Cache the family data - partners
        self.logger.debug(f"Caching {len(partnerships)} partnerships from partnerships")
        for i in partnerships:
            FamilyTreeMember(discord_id=i['user_id'], children=[], parent_id=None, partner_id=i['partner_id'], guild_id=i['guild_id'])

        # - children
        self.logger.debug(f"Caching {len(parents)} parents/children from parents")
        for i in parents:
            parent = FamilyTreeMember.get(i['parent_id'], i['guild_id'])
            parent._children.append(i['child_id'])
            child = FamilyTreeMember.get(i['child_id'], i['guild_id'])
            child._parent = i['parent_id']

        # Disconnect from the database
        await db.disconnect()

        # Save all available names to redis
        async with self.redis() as re:
            for user in self.users:
                await re.set(f'UserName-{user.id}', str(user))

        # And update DBL
        await self.post_guild_count()

    async def on_message(self, message):
        """Overriding the default on_message event to push my own context"""

        # Be mean to bots
        if message.author.bot:
            return

        # Invoke context
        ctx: CustomContext = await self.get_context(message, cls=CustomContext)

        # Add timeout to all commands - 2 minutes or bust
        try:
            await wait_for(self.invoke(ctx), 120.0)
        except AsyncioTimeoutError:
            await ctx.send(
                f"{message.author.mention}, your command has been "
                "cancelled for taking longer than 120 seconds to process.",
                embeddify=False,
                ignore_error=True
            )

    async def get_name(self, user_id:int):
        """Tries its best to grab a name for a user - firstly from the bot cache,
        secontly from the shallow users cache, thirdly from Redis, and then finally
        from HTTP

        Params:
            user_id: int
                The ID for the user whose name you want to get
        """

        user = self.get_user(user_id) or self.shallow_users.get(user_id)

        # See if it's a user in a guild this instance handles
        if user and isinstance(user, (discord.User, discord.ClientUser, discord.Member)):
            return str(user)

        # See if it's something I already cached
        if user:
            if user[1] > 0:
                self.shallow_users[user_id] = (user[0], user[1] - 1, user[2])
                # name, age, get_http_when_expires
                return str(user[0])

        # Try and get the username from Redis
        async with self.redis() as re:
            data = await re.get(f'UserName-{user_id}')

        # If there's no data:
        if data is None or (user and user[2]):
            # Get over HTTP
            try:
                name = await self.fetch_user(user_id)
            except discord.Forbidden:
                name = f'DELETED USER'
            # Cache
            self.shallow_users[user_id] = (str(name), 10, False)
            async with self.redis() as re:
                await re.set(f"UserName-{user_id}", str(name))
            return str(name)

        # There was redis data
        else:
            self.shallow_users[user_id] = (data, 10, True)
            return data

    def get_uptime(self) -> float:
        """Get the uptime of the bot in seconds"""

        return (dt.now() - self.startup_time).total_seconds()

    @property
    def owners(self) -> list:
        """Get a list of the owners from the config file"""

        return self.config['owners']


    def get_extensions(self) -> list:
        """Grab a list of loadable cogs from the cogs dir using blob"""

        ext = glob('cogs/[!_]*.py')
        rand = []
        extensions = [i.replace('\\', '.').replace('/', '.')[:-3] for i in ext + rand]
        self.logger.debug("Getting all extensions: " + str(extensions))
        return extensions


    def load_all_extensions(self):
        """Loads all the given extensions into the bot"""

        self.logger.debug('Unloading extensions... ')
        for i in self.get_extensions():
            try:
                self.unload_extension(i)
            except discord.ext.commands.ExtensionNotLoaded as e:
                self.logger.debug(f" * {i} :: not loaded")
            else:
                self.logger.debug(f" * {i} :: success")
        self.logger.debug('Loading extensions... ')
        for i in self.get_extensions():
            try:
                self.load_extension(i)
            except Exception as e:
                self.logger.critical(f"Error loading {i}")
                raise e
            self.logger.debug(f" * {i} :: success")

    async def set_default_presence(self, shard_id:int=None):
        """Sets the default presence for the bot as it appears in the config

        Params:
            shard_id: int = None
                If given, the bot will set the presence for only the shard ID
                If None, then the presence will be set for the whole instance
        """

        presence_text = self.config['presence_text']
        if shard_id:
            game = discord.Game(f"{presence_text} (shard {shard_id})".strip())
            await self.change_presence(activity=game, shard_id=shard_id)
        elif self.shard_ids:
            for i in self.shard_ids:
                game = discord.Game(f"{presence_text} (shard {i})".strip())
                await self.change_presence(activity=game, shard_id=i)
        else:
            game = discord.Game(f"{presence_text} (shard 0)".strip())
            await self.change_presence(activity=game)

    async def post_guild_count(self):
        """Post the average guild count to DiscordBots.org"""

        # Only post if there's actually a DBL token set
        if self.shard_count > 1 and 0 not in self.shard_ids:
            return
        if not self.config.get('dbl_token'):
            self.logger.warning("No DBL token has been provided")
            return

        url = f'https://discordbots.org/api/bots/{self.user.id}/stats'
        data = {
            'server_count': int((len(self.guilds) / len(self.shard_ids)) * self.shard_count),
            'shard_count': self.shard_count,
            'shard_id': 0,
        }
        headers = {
            'Authorization': self.config['dbl_token']
        }
        self.logger.info(f"Sending POST request to DBL with data {json.dumps(data)}")
        async with self.session.post(url, json=data, headers=headers) as r:
            pass

    def reload_config(self):
        """Opens the config file, loads it (as TOML) and stores it in Bot.config"""

        self.logger.debug("Reloading config")
        with open(self.config_file) as a:
            self.config = toml.load(a)

    def run(self, *args, **kwargs):
        """The original run method for the bot, using the token from config"""

        super().run(self.config['token'], *args, **kwargs)

    async def start(self, token:str=None, *args, **kwargs):
        """The original start method from the bot, using the token from the config
        and running the bot startup method with it"""

        self.logger.debug("Running startup method")
        self.startup_method = self.loop.create_task(self.startup())
        self.logger.debug("Running original D.py start method")
        await super().start(token or self.config['token'], *args, **kwargs)

    async def logout(self, *args, **kwargs):
        """The original bot logout method, but with the addition of closing the
        aiohttp ClientSession that was opened on bot creation"""

        self.logger.debug("Closing aiohttp ClientSession")
        await self.session.close()
        self.logger.debug("Running original D.py logout method")
        await super().logout(*args, **kwargs)
