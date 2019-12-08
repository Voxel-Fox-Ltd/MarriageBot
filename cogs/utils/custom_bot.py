from datetime import datetime as dt
import asyncio
import glob
import re as regex
import logging
from urllib.parse import urlencode
import collections
import typing
import json

import aiohttp
import discord
from discord.ext import commands
import toml

from cogs import utils


def get_prefix(bot, message:discord.Message):
    """Gives the prefix for the bot for a given guild"""

    # Try and get their guild settings from the bot
    try:
        settings = bot.guild_settings.get(message.guild.id, bot.default_guild_settings)
    except AttributeError:
        settings = bot.default_guild_settings
    x = settings['prefix']

    # If we don't respect custom prefixes, go back to the default
    if not bot.config['prefix']['respect_custom']:
        x = bot.config['prefix']['default_prefix']

    # Allow mentions
    return commands.when_mentioned_or(x)(bot, message)


class CustomBot(commands.AutoShardedBot):
    """A fancy-ass verison of the normal AutoShardedBot
    I've stuck a bunch of stuff inside it so it's easier for me to use
    for my stuff, but ultimately it's the same ol' AutoShardedBot that the
    library provides to start with"""

    def __init__(self, *args, config_file:str, logger:logging.Logger=None, **kwargs):
        super().__init__(command_prefix=get_prefix, *args, **kwargs)

        # Throw down the root logger
        self.logger: logging.Logger = logger or logging.getLogger()

        # Cache the config
        self.config: dict = None
        self.config_file: str = config_file
        self.reload_config()
        self.default_guild_settings = {'prefix': self.config['prefix']['default_prefix'], 'allow_incest': False}

        # Set up arguments that are used in cogs and stuff
        self.bad_argument = regex.compile(r'(User|Member) "(.*)" not found')  # TODO put this into a method
        self._invite_link = None  # populated by 'invite' property
        self.support_guild = None  # populated by Patreon or bot mod check

        # Set up stuff that'll be used bot-wide
        self.shallow_users: typing.Dict[int, utils.ShallowUser] = {}  # A shallow copy of users' names
        self.session = aiohttp.ClientSession(loop=self.loop)  # Session for DBL post
        self.startup_time = dt.now()  # Store when the instance was created
        self.startup_method = None  # Store the startup task so I can see if it err'd

        # Set up stuff that'll be used literally everywhere
        self.database = utils.DatabaseConnection
        utils.DatabaseConnection.logger = self.logger.getChild("database")
        self.redis = utils.RedisConnection
        utils.RedisConnection.logger = self.logger.getChild("redis")

        # Set up some caches
        self.server_specific_families: typing.List[int] = []  # List of whitelisted guild IDs
        self.proposal_cache: typing.Dict[int, tuple] = utils.ProposalCache()
        self.blacklisted_guilds: typing.List[int] = []  # List of blacklisted guid IDs
        self.blocked_users: typing.Dict[int, typing.List[int]] = collections.defaultdict(list)  # uid: [blocked uids]
        self.guild_settings: typing.Dict[int, dict] = collections.defaultdict(lambda: self.default_guild_settings.copy())
        self.dbl_votes: typing.Dict[int, dt] = {}

        # Put the bot object in some other classes
        utils.ProposalCache.bot = self
        utils.random_text.RandomText.original.bot = self

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
            'permissions': permissions.value,
            'redirect_uri': self.config['oauth']['join_server_redirect_uri'],
        })
        return self._invite_link

    def invite_link_to_guild(self, guild_id:int):
        """Returns an invite link to a guild
        Used for the website to easily add the bot to a given guild

        Params:
            guild_id: int
                The ID for the guild the invite link should default to
        """

        return self.invite_link + f'&guild_id={guild_id}'

    @property
    def is_server_specific(self) -> bool:
        """Whether or not the BOT is running the server specific version"""

        return self.config['server_specific']

    def allows_incest(self, guild:typing.Union[discord.Guild, int]) -> bool:
        """Returns if a given GUILD allows incest or not

        Params:
            guild_id: int
                The ID for the guild you want to check against
        """

        guild_id = getattr(guild, 'id', guild)
        return self.is_server_specific and guild_id in self.guild_settings and self.guild_settings[guild_id]['allow_incest']

    async def startup(self):
        """The startup method for the bot - clears all the caches and reads
        everything out again from the database, essentially starting anew
        as if rebooted"""

        # Remove caches
        self.logger.debug("Clearing family tree member cache")
        utils.FamilyTreeMember.all_users.clear()
        self.logger.debug("Clearing blacklisted guilds cache")
        self.blacklisted_guilds.clear()
        self.logger.debug("Clearing guild settings cache")
        self.guild_settings.clear()
        self.logger.debug("Clearing DBL votes cache")
        self.dbl_votes.clear()
        self.logger.debug("Clearing blocked users cache")
        self.blocked_users.clear()
        self.logger.debug("Clearing random text cache")
        utils.random_text.RandomText.original.all_random_text.clear()

        # Grab a database connection
        db: utils.DatabaseConnection = await self.database.get_connection()

        # Load in all of the random text
        try:
            random_text = await db('SELECT * FROM random_text')
        except Exception as e:
            self.logger.critical(f"Ran into an errorr selecting random text: {e}")
            exit(1)
        self.logger.debug(f"Caching {len(random_text)} lines of random text")
        for row in random_text:
            utils.random_text.RandomText.original.all_random_text[row['command_name']][row['event_name']].append(row['string'])

        # Pick up the blacklisted guilds from the db
        try:
            blacklisted = await db('SELECT * FROM blacklisted_guilds')
        except Exception as e:
            self.logger.critical(f"Ran into an error selecting blacklisted guilds: {e}")
            exit(1)
        self.logger.debug(f"Caching {len(blacklisted)} blacklisted guilds")
        self.blacklisted_guilds = [i['guild_id'] for i in blacklisted]

        # Pick up the blocked users
        try:
            blocked = await db('SELECT * FROM blocked_user')
        except Exception as e:
            self.logger.critical(f"Ran into an error selecting blocked users: {e}")
            exit(1)
        self.logger.debug(f"Caching {len(blocked)} blocked users")
        for user in blocked:
            self.blocked_users[user['user_id']].append(user['blocked_user_id'])

        # Grab the command prefixes per guild
        try:
            all_settings = await db('SELECT * FROM guild_settings')
        except Exception as e:
            self.logger.critical(f"Ran into an error selecting guild settings: {e}")
            exit(1)
        self.logger.debug(f"Caching {len(all_settings)} guild settings")
        for items in all_settings:
            current_settings = self.guild_settings[items]  # Get current (which should include defaults)
            current_settings.update(**dict(items))  # Update from db
            if self.is_server_specific:
                current_settings['prefix'] = current_settings['gold_prefix']
            self.guild_settings[items['guild_id']] = current_settings  # Cache

        # Grab the last vote times of each user
        try:
            votes = await db("SELECT * FROM dbl_votes WHERE timestamp > NOW() - INTERVAL '12 hours'")
        except Exception as e:
            self.logger.critical(f"Ran into an error selecting DBL votes: {e}")
            exit(1)
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
                self.logger.critical(f"Ran into an error selecting server specific guilds: {e}")
                exit(1)
            allowed_guild_ids = [i['guild_id'] for i in allowed_guilds]
            current_guild_ids = self._connection._guilds.keys()
            guild_ids_to_leave = [i for i in current_guild_ids if i not in allowed_guild_ids]
            for guild_id in guild_ids_to_leave:
                guild = self.get_guild(guild_id)
                self.logger.warn(f"Automatically left guild {guild.name} ({guild.id}) for non-subscription")
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
            self.logger.critical(f"Ran into an error selecting either marriages or parents: {e}")
            exit(1)

        # Cache the family data - partners
        self.logger.debug(f"Caching {len(partnerships)} partnerships from partnerships")
        for i in partnerships:
            utils.FamilyTreeMember(discord_id=i['user_id'], children=[], parent_id=None, partner_id=i['partner_id'], guild_id=i['guild_id'])

        # - children
        self.logger.debug(f"Caching {len(parents)} parents/children from parents")
        for i in parents:
            parent = utils.FamilyTreeMember.get(i['parent_id'], i['guild_id'])
            parent._children.append(i['child_id'])
            child = utils.FamilyTreeMember.get(i['child_id'], i['guild_id'])
            child._parent = i['parent_id']

        # Disconnect from the database
        await db.disconnect()

        # Save all available names to redis
        async with self.redis() as re:
            for user in self.users:
                await re.set(f'UserName-{user.id}', str(user))

        # And update DBL
        await self.post_guild_count()

    async def on_message(self, message:discord.Message):
        """Overriding the default on_message event to push my own context"""

        # Be mean to bots
        if message.author.bot:
            return

        # Invoke context
        ctx: utils.Context = await self.get_context(message, cls=utils.Context)

        # Add timeout to all commands - 2 minutes or bust
        try:
            await asyncio.wait_for(self.invoke(ctx), 120.0)
        except asyncio.TimeoutError:
            await ctx.send(
                f"{message.author.mention}, your command has been cancelled for taking longer than 120 seconds to process.",
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

        user = self.get_user(user_id)
        if user:
            return str(user)
        user = self.shallow_users.get(user_id)
        if user is None:
            user = utils.ShallowUser(user_id)
            self.shallow_users[user_id] = user
        return await user.get_name(self)

    def get_uptime(self) -> float:
        """Gets the total time since the class was initialised (in seconds)"""

        return (dt.now() - self.startup_time).total_seconds()

    @property
    def owners(self) -> list:
        """Get a list of the owners from the config file"""

        return self.config.get('owners', list())

    async def fetch_support_guild(self):
        """Fetches the guild object for the given support guild in the config file, storing it
        locally in bot.support_guild"""

        guild_id = self.config.get('guild_id')
        if guild_id in [None, '']:
            self.logger.warn("No guild ID set in the bot config")
        guild = await self.fetch_guild(guild_id)
        self.support_guild = guild

    def get_extensions(self) -> typing.List[str]:
        """Gets a list of the extensions that are to be loaded into the bot"""

        ext = glob.glob('cogs/[!_]*.py')
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

        presence_text = self.config.get('presence_text')
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

        # Only shard 0 can post
        if self.shard_count > 1 and 0 not in self.shard_ids:
            return

        # Only post if there's actually a DBL token set
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

    async def login(self, token:str=None, *args, **kwargs):
        await super().login(token or self.config['token'], *args, **kwargs)

    async def start(self, token:str=None, *args, **kwargs):
        """The original start method from the bot, using the token from the config
        and running the bot startup method with it"""

        self.logger.debug("Running startup method")
        self.startup_method = self.loop.create_task(self.startup())
        self.logger.debug("Running original D.py start method")
        await super().start(token or self.config['token'], *args, **kwargs)

    async def close(self, *args, **kwargs):
        """The original bot close method, but with the addition of closing the
        aiohttp ClientSession that was opened on bot creation"""

        self.logger.debug("Closing aiohttp ClientSession")
        await asyncio.wait_for(self.session.close(), timeout=None)
        self.logger.debug("Running original D.py logout method")
        await super().close(*args, **kwargs)
