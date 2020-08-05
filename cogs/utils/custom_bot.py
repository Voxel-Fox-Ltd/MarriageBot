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

from cogs.utils import random_text
from cogs.utils.custom_context import CustomContext
from cogs.utils.database import DatabaseConnection
from cogs.utils.family_tree.family_tree_member import FamilyTreeMember
from cogs.utils.proposal_cache import ProposalCache
from cogs.utils.redis import RedisConnection
from cogs.utils.shallow_user import ShallowUser


def get_prefix(bot, message:discord.Message):
    """Gives the prefix for the bot for a given guild"""

    # Try and get their guild settings from the bot
    try:
        settings = bot.guild_settings.get(message.guild.id, bot.DEFAULT_GUILD_SETTINGS.copy())
    except AttributeError:
        settings = bot.DEFAULT_GUILD_SETTINGS.copy()
    x = settings['prefix']

    # If we don't respect custom prefixes, go back to the default
    if not bot.config['prefix']['respect_custom']:
        x = bot.config['prefix']['default_prefix']

    # Allow mentions
    if x in ["'", "‘"]:
        x = ["'", "‘"]
    x = [x] if isinstance(x, str) else x
    return commands.when_mentioned_or(*x)(bot, message)


class CustomBot(commands.AutoShardedBot):
    """A fancy-ass verison of the normal AutoShardedBot
    I've stuck a bunch of stuff inside it so it's easier for me to use
    for my stuff, but ultimately it's the same ol' AutoShardedBot that the
    library provides to start with"""

    def __init__(self, *args, config_file:str, logger:logging.Logger=None, **kwargs):
        """The initialiser for the bot object
        Note that we load the config before running the original method"""

        # Store the config file for later
        self.config = None
        self.config_file = config_file
        self.logger = logger or logging.getLogger("bot")
        self.reload_config()

        # Set up config
        self.DEFAULT_GUILD_SETTINGS = {
            'prefix': self.config['prefix']['default_prefix'],  # Set in init
            'allow_incest': False,  # Only used in gold
            'max_family_members': self.config['max_family_members'],  # Set in init; only used in gold
            'max_children': {},  # RoleID: ChildAmount; only used in gold
            'gifs_enabled': True,  # Whether or not to add gifs to the simulation commands
        }

        # Run original
        super().__init__(command_prefix=get_prefix, guild_subscriptions=self.is_server_specific, *args, **kwargs)

        # Set up arguments that are used in cogs and stuff
        self._invite_link = None  # populated by 'invite' property
        self.support_guild = None  # populated by Patreon or bot mod check

        # Set up stuff that'll be used bot-wide
        self.shallow_users: typing.Dict[int, ShallowUser] = {}  # A shallow copy of users' names
        self.session = aiohttp.ClientSession(loop=self.loop)  # Session for DBL post
        self.startup_time = dt.now()  # Store when the instance was created
        self.startup_method = None  # Store the startup task so I can see if it err'd

        # Set up stuff that'll be used literally everywhere
        self.database = DatabaseConnection
        DatabaseConnection.logger = self.logger.getChild("database")
        self.redis = RedisConnection
        RedisConnection.logger = self.logger.getChild("redis")

        # Set up some caches
        self.server_specific_families: typing.List[int] = []  # List of whitelisted guild IDs
        self.proposal_cache: typing.Dict[int, tuple] = ProposalCache()
        self.blacklisted_guilds: typing.List[int] = []  # List of blacklisted guid IDs
        self.blocked_users: typing.Dict[int, typing.List[int]] = collections.defaultdict(list)  # uid: [blocked uids]
        self.guild_settings: typing.Dict[int, dict] = collections.defaultdict(lambda: copy.deepcopy(self.DEFAULT_GUILD_SETTINGS))
        # self.user_settings = collections.defaultdict(self.DEFAULT_USER_SETTINGS.copy)
        self.dbl_votes: typing.Dict[int, dt] = {}

        # Put the bot object in some other classes
        ProposalCache.bot = self
        random_text.RandomText.original.bot = self

    async def startup(self):
        """The startup method for the bot - clears all the caches and reads
        everything out again from the database, essentially starting anew
        as if rebooted"""

        # Remove caches
        self.logger.info("Clearing family tree member cache")
        FamilyTreeMember.all_users.clear()
        self.logger.info("Clearing blacklisted guilds cache")
        self.blacklisted_guilds.clear()
        self.logger.info("Clearing guild settings cache")
        self.guild_settings.clear()
        self.logger.info("Clearing DBL votes cache")
        self.dbl_votes.clear()
        self.logger.info("Clearing blocked users cache")
        self.blocked_users.clear()
        self.logger.info("Clearing random text cache")
        random_text.RandomText.original.all_random_text.clear()

        # Grab a database connection
        db: DatabaseConnection = await self.database.get_connection()

        # Load in all of the random text
        try:
            text_lines = await db('SELECT * FROM random_text')
        except Exception as e:
            self.logger.critical(f"Ran into an errorr selecting random text: {e}")
            exit(1)
        self.logger.info(f"Caching {len(text_lines)} lines of random text")
        for row in text_lines:
            random_text.RandomText.original.all_random_text[row['command_name']][row['event_name']].append(row['string'])

        # Pick up the blacklisted guilds from the db
        try:
            blacklisted = await db('SELECT * FROM blacklisted_guilds')
        except Exception as e:
            self.logger.critical(f"Ran into an error selecting blacklisted guilds: {e}")
            exit(1)
        self.logger.info(f"Caching {len(blacklisted)} blacklisted guilds")
        self.blacklisted_guilds = [i['guild_id'] for i in blacklisted]

        # Pick up the blocked users
        try:
            blocked = await db('SELECT * FROM blocked_user')
        except Exception as e:
            self.logger.critical(f"Ran into an error selecting blocked users: {e}")
            exit(1)
        self.logger.info(f"Caching {len(blocked)} blocked users")
        for user in blocked:
            self.blocked_users[user['user_id']].append(user['blocked_user_id'])

        # Grab the command prefixes per guild
        try:
            all_settings = await db('SELECT * FROM guild_settings WHERE (guild_id >> 22) % $1=ANY($2::INTEGER[])', self.shard_count, self.shard_ids)
        except Exception as e:
            self.logger.critical(f"Ran into an error selecting guild settings: {e}")
            exit(1)
        self.logger.info(f"Caching {len(all_settings)} guild settings")
        for items in all_settings:
            current_settings = self.guild_settings[items['guild_id']]  # Get current (which should include defaults)
            current_settings.update(**dict(items))  # Update from db
            if self.is_server_specific:
                current_settings['prefix'] = current_settings['gold_prefix']
            self.guild_settings[items['guild_id']] = current_settings  # Cache

        # Grab the max children amount
        if self.is_server_specific:
            try:
                max_children_data = await db('SELECT * FROM max_children_amount WHERE (guild_id >> 22) % $1=ANY($2::INTEGER[])', self.shard_count, self.shard_ids)
            except Exception as e:
                self.logger.critical(f"Ran into an error selecting guild settings: {e}")
                exit(1)
            self.logger.info(f"Caching {len(max_children_data)} max children settings")
            for row in max_children_data:
                current_settings = self.guild_settings[row['guild_id']]  # Get current (which should include defaults)
                current_settings['max_children'][row['role_id']] = row['amount']
                self.guild_settings[row['guild_id']] = current_settings  # Cache

        # Grab the last vote times of each user
        try:
            votes = await db("SELECT * FROM dbl_votes WHERE timestamp > NOW() - INTERVAL '12 hours'")
        except Exception as e:
            self.logger.critical(f"Ran into an error selecting DBL votes: {e}")
            exit(1)
        self.logger.info(f"Caching {len(votes)} DBL votes")
        for v in votes:
            self.dbl_votes[v['user_id']] = v['timestamp']

        # Wait for the bot to cache users before continuing
        self.logger.info("Waiting until ready before completing startup method.")
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
                self.logger.info(f"Automatically left guild {guild.name} ({guild.id}) for non-subscription")
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
        self.logger.info(f"Caching {len(partnerships)} partnerships from partnerships")
        for i in partnerships:
            FamilyTreeMember(discord_id=i['user_id'], children=[], parent_id=None, partner_id=i['partner_id'], guild_id=i['guild_id'])

        # - children
        self.logger.info(f"Caching {len(parents)} parents/children from parents")
        for i in parents:
            parent = FamilyTreeMember.get(i['parent_id'], i['guild_id'])
            parent._children.append(i['child_id'])
            child = FamilyTreeMember.get(i['child_id'], i['guild_id'])
            child._parent = i['parent_id']

        # Disconnect from the database
        await db.disconnect()

        # # Save all available names to redis
        # async with self.redis() as re:
        #     for user in self.users:
        #         await re.set(f'UserName-{user.id}', str(user))

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

    async def fetch_support_guild(self):
        """Gets and stores the support guild defined in the bot settings"""

        self.support_guild = self.get_guild(self.config['guild_id']) or await self.fetch_guild(self.config['guild_id'])
        return self.support_guild

    @property
    def is_server_specific(self) -> bool:
        """Whether or not the BOT is running the server specific version"""

        return self.config['server_specific']

    def get_max_family_members(self, guild:discord.Guild) -> int:
        """Whether or not the BOT is running the server specific version"""

        return self.guild_settings[guild.id]['max_family_members'] if self.is_server_specific else self.config['max_family_members']

    def allows_incest(self, guild:typing.Union[discord.Guild, int]) -> bool:
        """Returns if a given GUILD allows incest or not

        Params:
            guild_id: int
                The ID for the guild you want to check against
        """

        guild_id = getattr(guild, 'id', guild)
        return self.is_server_specific and guild_id in self.guild_settings and self.guild_settings[guild_id]['allow_incest']

    async def on_message(self, message:discord.Message):
        """Overriding the default on_message event to push my own context"""

        # Be mean to bots
        if message.author.bot:
            return

        # Invoke context
        ctx: CustomContext = await self.get_context(message, cls=CustomContext)

        # Add timeout to all commands - 2 minutes or bust
        try:
            await asyncio.wait_for(self.invoke(ctx), 120.0)
        except asyncio.TimeoutError:
            await ctx.send(
                f"{message.author.mention}, your command has been cancelled for taking longer than 120 seconds to process.",
                embeddify=False,
                ignore_error=True
            )

    async def get_name(self, user_id:int, fetch_from_api:bool=False):
        """Tries its best to grab a name for a user - firstly from the bot cache,
        secontly from the shallow users cache, thirdly from Redis, and then finally
        from HTTP

        Params:
            user_id: int
                The ID for the user whose name you want to get
        """

        user = self.shallow_users.get(user_id)
        if user is None:
            user = ShallowUser(user_id)
            self.shallow_users[user_id] = user
        if fetch_from_api:
            return await user.fetch_from_api(self)
        return await user.get_name(self)

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
                self.logger.info(f' * {i}... failed - {e!s}')
            else:
                self.logger.info(f' * {i}... success')

        # Now load em up again
        self.logger.info('Loading extensions... ')
        for i in self.get_extensions():
            try:
                self.load_extension(i)
            except Exception as e:
                self.logger.critical(f"Error loading {i}")
                raise e
            self.logger.info(f" * {i} :: success")

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
                try:
                    await self.change_presence(activity=activity, status=status, shard_id=i)
                except KeyError:
                    self.logger.info(f"Encountered KeyError on setting presence in shard {i}")
                    pass  # Library error so we'll just discard it

        # Not sharded - just do everywhere
        else:
            activity = discord.Activity(
                name=presence['text'],
                type=getattr(discord.ActivityType, presence['activity_type'].lower())
            )
            status = getattr(discord.Status, presence['status'].lower())
            await self.change_presence(activity=activity, status=status)

    def reload_config(self):
        """Opens the config file, loads it (as TOML) and stores it in Bot.config"""

        self.logger.info("Reloading config")
        try:
            with open(self.config_file) as a:
                self.config = toml.load(a)
        except Exception as e:
            self.logger.critical(f"Couldn't read config file - {e}")
            exit(1)

    async def login(self, token:str=None, *args, **kwargs):
        await super().login(token or self.config['token'], *args, **kwargs)

    async def start(self, token:str=None, *args, **kwargs):
        """The original start method from the bot, using the token from the config
        and running the bot startup method with it"""

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

        self.logger.info("Closing aiohttp ClientSession")
        await asyncio.wait_for(self.session.close(), timeout=None)
        self.logger.info("Running original D.py logout method")
        await super().close(*args, **kwargs)
