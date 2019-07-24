from datetime import datetime as dt
from importlib import import_module
from asyncio import sleep, create_subprocess_exec, TimeoutError as AsyncioTimeoutError, wait_for
from glob import glob
from re import compile
import logging
from urllib.parse import urlencode
from collections import defaultdict

from aiohttp import ClientSession
from aiohttp.web import Application, AppRunner, TCPSite
from discord import Game, Message, Permissions, User, ClientUser, Member
from discord.ext.commands import AutoShardedBot, when_mentioned_or, cooldown
from discord.ext.commands.cooldowns import BucketType
import ujson as json

from cogs.utils.database import DatabaseConnection
from cogs.utils.redis import RedisConnection
from cogs.utils.family_tree.family_tree_member import FamilyTreeMember
from cogs.utils.customised_tree_user import CustomisedTreeUser
from cogs.utils.proposal_cache import ProposalCache
from cogs.utils.tree_cache import TreeCache
from cogs.utils.custom_context import CustomContext


logger = logging.getLogger('marriagebot.bot')


def get_prefix(bot, message:Message):
    '''
    Gives the prefix for the given guild
    '''

    try:
        x = bot.guild_prefixes.get(message.guild.id, bot.config['prefix']['default_prefix'])
    except AttributeError:
        x = bot.config['prefix']['default_prefix']
    if not bot.config['prefix']['respect_custom']:
        x = bot.config['prefix']['default_prefix']
    return when_mentioned_or(x)(bot, message)


class CustomBot(AutoShardedBot):

    def __init__(self, config_file:str='config/config.json', *args, **kwargs):
        '''Make the bot WEW'''

        # Get the command prefix from the kwargs
        if kwargs.get('command_prefix'):
            super().__init__(*args, **kwargs)
        else:
            super().__init__(command_prefix=get_prefix, *args, **kwargs)

        # Hang out and make all the stuff I'll need
        self.config: dict = None  # the config dict - None until reload_config() is sucessfully called
        self.config_file = config_file  # the config filename - used in reload_config()
        self.reload_config()  # populate bot.config 
        self.bad_argument = compile(r'(User|Member) "(.*)" not found')  # bad argument regex converter
        self._invite_link = None  # the invite for the bot - dynamically generated
        self.shallow_users = {}  # id: (User, age) - age is how long until it needs re-fetching from Discord
        self.support_guild = None  # the support guild - populated by patreon check and event log
        self.session = ClientSession(loop=self.loop)  # aiohttp session for get/post requests
        self.database = DatabaseConnection  # database connection class 
        self.redis = RedisConnection  # redis connection class 
        self.server_specific_families = []  # list[guild_id] - guilds that have server-specific families attached
        FamilyTreeMember.bot = self
        CustomisedTreeUser.bot = self
        ProposalCache.bot = self
        TreeCache.bot = self
        self.startup_time = dt.now()  # store bot startup time
        self.startup_method = None  # store startup method so I can see errors in it 
        self.deletion_method = None  # store deletion method so I can cancel it on shutdown
        self.proposal_cache = ProposalCache()  # cache for users who've been proposed to/are proposing
        self.blacklisted_guilds = []  # a list of guilds that are blacklisted by the bot
        self.blocked_users = defaultdict(list) # user_id: list(user_id) - users who've blocked other users
        self.guild_prefixes = {}  # guild_id: prefix - custom prefixes per guild
        self.dbl_votes = {}  # uid: timestamp (of last vote) - cast dbl votes
        self.tree_cache = TreeCache()  # cache of users generating trees
        cooldown(1, 5, BucketType.user)(self.get_command('help'))  # add cooldown to help command


    @property 
    def invite_link(self):
        '''The invite link for the bot'''

        if self._invite_link: return self._invite_link
        permissions = Permissions()
        permissions.read_messages = True 
        permissions.send_messages = True 
        permissions.embed_links = True 
        permissions.attach_files = True 
        self._invite_link = 'https://discordapp.com/oauth2/authorize?' + urlencode({
            'client_id': self.user.id,
            'scope': 'bot',
            'permissions': permissions.value
        })
        return self._invite_link


    def invite_link_to_guild(self, guild_id:int):
        '''Returns an invite link with additional guild ID param'''

        return self.invite_link + f'&guild_id={guild_id}'


    async def startup(self):
        '''Resets and fills the FamilyTreeMember cache with objects'''

        # Remove caches
        logger.debug("Clearing caches")
        FamilyTreeMember.all_users.clear()
        CustomisedTreeUser.all_users.clear()
        self.blacklisted_guilds.clear() 
        self.guild_prefixes.clear() 
        self.dbl_votes.clear() 
        self.blocked_users.clear() 

        db: DatabaseConnection = await self.database.get_connection()
        
        # Pick up the blacklisted guilds from the db
        blacklisted = await db('SELECT * FROM blacklisted_guilds')
        logger.debug(f"Caching {len(blacklisted)} blacklisted guilds")
        self.blacklisted_guilds = [i['guild_id'] for i in blacklisted]

        # Pick up the blocked users
        blocked = await db('SELECT * FROM blocked_user')
        logger.debug(f"Caching {len(blocked)} blocked users")
        for user in blocked:
            self.blocked_users[user['user_id']].append(user['blocked_user_id'])

        # Grab the command prefixes per guild
        settings = await db('SELECT * FROM guild_settings')
        logger.debug(f"Caching {len(settings)} guild settings")
        for guild_setting in settings:
            self.guild_prefixes[guild_setting['guild_id']] = guild_setting['prefix']

        # Grab the last vote times of each user 
        votes = await db('SELECT * FROM dbl_votes')
        logger.debug(f"Caching {len(votes)} DBL votes")
        for v in votes:
            self.dbl_votes[v['user_id']] = v['timestamp']

        # Wait for the bot to cache users before continuing
        logger.debug("Waiting until ready before completing startup method.")
        await self.wait_until_ready()

        # Look through and find what servers the bot is allowed to be on, if server specific
        if self.config['server_specific']:
            allowed_guilds = await db('SELECT guild_id FROM guild_specific_families')
            allowed_guild_ids = [i['guild_id'] for i in allowed_guilds]
            current_guild_ids = self._connection._guilds.keys()
            guild_ids_to_leave = [i for i in current_guild_ids if i not in allowed_guild_ids]
            for guild_id in guild_ids_to_leave:
                guild = self.get_guild(guild_id)
                await guild.leave()

        # Get family data from database
        if self.config['server_specific']:
            partnerships = await db('SELECT * FROM marriages WHERE guild_id<>0')
            parents = await db('SELECT * FROM parents WHERE guild_id<>0')
        else:
            partnerships = await db('SELECT * FROM marriages WHERE guild_id=0')
            parents = await db('SELECT * FROM parents WHERE guild_id=0')
        customisations = await db('SELECT * FROM customisation')
        
        # Cache the family data - partners
        logger.debug(f"Caching {len(partnerships)} partnerships from partnerships")
        for i in partnerships:
            FamilyTreeMember(discord_id=i['user_id'], children=[], parent_id=None, partner_id=i['partner_id'], guild_id=i['guild_id'])

        # - children
        logger.debug(f"Caching {len(parents)} parents/children from parents")
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
        '''Use custom context for commands'''

        # Be mean to bots
        if message.author.bot:
            return

        # Invoke context
        ctx: CustomContext = await self.get_context(message, cls=CustomContext)

        # Add timeout to all commands - 2 minutes or bust
        try:
            await wait_for(self.invoke(ctx), 120.0)
        except AsyncioTimeoutError:
            await ctx.send(f"{message.author.mention}, your command has been cancelled for taking longer than 120 seconds to process.", embeddify=False, ignore_error=True)

    
    async def get_name(self, user_id):
        '''Gets the name for a user - first from cache, then from redis, then from HTTP'''

        user = self.get_user(user_id) or self.shallow_users.get(user_id)

        # See if it's a user in a guild this instance handles
        if user and isinstance(user, (User, ClientUser, Member)):
            return str(user)
        
        # See if it's something I already cached
        elif user:
            if user[1] > 0:
                self.shallow_users[user_id] = [user[0], user[1] - 1] 
                return str(user[0])

        # See if it's in the Redis
        async with self.redis() as re:
            data = await re.get(f'UserName-{user_id}')

        # It isn't - fetch user
        if data == None:
            try:
                name = await self.fetch_user(user_id)
            except Exception:
                name = f'<DELETED {user_id}>'
            self.shallow_users[user_id] = [name, 20]
            return str(name)

        # It is - cache and return
        else:
            self.shallow_users[user_id] = [data, 20]
            return data


    def get_uptime(self) -> float:
        '''Gets the uptime of the bot in seconds'''

        return (dt.now() - self.startup_time).total_seconds()


    @property 
    def owners(self) -> list:
        return self.config['owners']


    def get_extensions(self) -> list:
        '''Gets the filenames of all the loadable cogs'''

        ext = glob('cogs/[!_]*.py')
        # rand = glob('cogs/utils/random_text/[!_]*.py')
        rand = []
        extensions = [i.replace('\\', '.').replace('/', '.')[:-3] for i in ext + rand]
        logger.debug("Getting all extensions: " + str(extensions))
        return extensions


    def load_all_extensions(self):
        '''Loads all extensions from .get_extensions()'''

        logger.debug('Unloading extensions... ')
        for i in self.get_extensions():
            log_string = f' * {i}... '
            try:
                self.unload_extension(i)
                log_string += 'sucess'
            except Exception as e:
                log_string += str(e)
            logger.debug(log_string)
        logger.debug('Loading extensions... ')
        for i in self.get_extensions():
            log_string = f' * {i}... '
            try:
                self.load_extension(i)
                log_string += 'sucess'
            except Exception as e:
                log_string += str(e)
            logger.debug(log_string)


    async def set_default_presence(self, shard_id:int=None):
        '''Sets the default presence of the bot as appears in the config file'''
        
        presence_text = self.config['presence_text']
        if self.shard_ids:
            for i in self.shard_ids:
                game = Game(f"{presence_text} (shard {i})".strip())
                await self.change_presence(activity=game, shard_id=i)
        else:
            game = Game(f"{presence_text} (shard 0)".strip())
            await self.change_presence(activity=game)


    async def post_guild_count(self):
        '''The loop of uploading the guild count to the DBL server'''

        # Only post if there's actually a DBL token set
        if not self.config.get('dbl_token'):
            return
        if self.shard_count > 1 and 0 not in self.shard_ids:
            return

        url = f'https://discordbots.org/api/bots/{self.user.id}/stats'
        json = {
            'server_count': int((len(self.guilds) / len(self.shard_ids)) * self.shard_count),
            'shard_count': self.shard_count,
            'shard_id': 0,
        }
        headers = {
            'Authorization': self.config['dbl_token']
        }
        logger.debug(f"Sending POST request to DBL with data {json.dumps(json)}")
        async with self.session.post(url, json=json, headers=headers) as r:
            pass


    async def delete_loop(self):
        '''A loop that runs every hour, deletes all files in the tree storage directory'''

        await self.wait_until_ready()
        while not self.is_closed: 
            logger.debug("Deleting all residual tree files")
            await create_subprocess_exec('rm', f'{self.config["tree_file_location"]}/*', loop=self.bot.loop)
            await sleep(60*60)


    async def destroy(self, user_id:int):
        '''Removes a user ID from the database and cache'''

        async with self.database() as db:
            await db.destroy(user_id)
        await FamilyTreeMember.get(user_id).destroy()


    def reload_config(self):
        '''Opens, loads, and stores the config from the given config file'''

        logger.debug("Reloading config")
        with open(self.config_file) as a:
            self.config = json.load(a)


    def run(self, *args, **kwargs):
        '''Runs the original bot run method with the config's token'''

        super().run(self.config['token'], *args, **kwargs)


    async def start(self, token:str=None, *args, **kwargs):
        '''Starts up the bot and whathaveyou'''

        logger.debug("Running startup method") 
        self.startup_method = self.loop.create_task(self.startup())
        # logger.debug("Starting delete loop")
        # self.deletion_method = self.loop.create_task(self.delete_loop())
        logger.debug("Running original D.py start method")
        await super().start(token or self.config['token'], *args, **kwargs)

    
    async def logout(self, *args, **kwargs):
        '''Logs out the bot and all of its started processes'''

        logger.debug("Closing aiohttp ClientSession")
        await self.session.close()
        logger.debug("Running original D.py logout method")
        await super().logout(*args, **kwargs)
