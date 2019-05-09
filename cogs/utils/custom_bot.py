from datetime import datetime as dt
from json import load
from importlib import import_module
from asyncio import sleep, create_subprocess_exec
from glob import glob
from re import compile
from logging import getLogger
from urllib.parse import urlencode

from aiohttp import ClientSession
from aiohttp.web import Application, AppRunner, TCPSite
from discord import Game, Message, Permissions, User
from discord.ext.commands import AutoShardedBot, when_mentioned_or, cooldown
from discord.ext.commands.cooldowns import BucketType

from cogs.utils.database import DatabaseConnection
from cogs.utils.redis import RedisConnection
from cogs.utils.family_tree.family_tree_member import FamilyTreeMember
from cogs.utils.customised_tree_user import CustomisedTreeUser
from cogs.utils.proposal_cache import ProposalCache
from cogs.utils.tree_cache import TreeCache
from cogs.utils.custom_context import CustomContext


logger = getLogger('marriagebot')


def get_prefix(bot, message:Message):
    '''
    Gives the prefix for the given guild
    '''

    try:
        x = bot.guild_prefixes.get(message.guild.id, bot.config['default_prefix'])
    except AttributeError:
        x = bot.config['default_prefix']
    return when_mentioned_or(x)(bot, message)


class CustomBot(AutoShardedBot):

    def __init__(self, config_file:str='config/config.json', commandline_args=None, *args, **kwargs):
        # Things I would need anyway
        if kwargs.get('command_prefix'):
            super().__init__(*args, **kwargs)
        else:
            super().__init__(command_prefix=get_prefix, *args, **kwargs)

        # Store the config file for later
        self.config = None
        self.config_file = config_file
        self.reload_config()
        self.commandline_args = commandline_args
        self.bad_argument = compile(r'(User|Member) "(.*)" not found')
        self._invite_link = None

        self.shallow_users = {}  # id: (User, age) - age is how long until it needs re-fetching from Discord
        self.support_guild = None

        # Aiohttp session for use in DBL posting
        self.session = ClientSession(loop=self.loop)

        # Allow database connections like this
        self.database = DatabaseConnection
        self.redis = RedisConnection

        # Allow get_guild and setup for server-specific trees
        self.server_specific_families = []  # list[guild_id]
        FamilyTreeMember.bot = self
        CustomisedTreeUser.bot = self
        ProposalCache.bot = self
        TreeCache.bot = self

        # Store the startup method so I can see if it completed successfully
        self.startup_time = dt.now()
        self.startup_method = None
        self.deletion_method = None

        # Add a cache for proposing users
        self.proposal_cache = ProposalCache()

        # Add a list of blacklisted guilds and users
        self.blacklisted_guilds = []
        self.blocked_users = {}  # user_id: list(user_id)

        # Dictionary of custom prefixes
        self.guild_prefixes = {}  # guild_id: prefix

        # See who voted for the bot and when
        self.dbl_votes = {}  # uid: timestamp (of last vote)

        self.tree_cache = TreeCache()
        
        # Add a cooldown to help
        cooldown(1, 5, BucketType.user)(self.get_command('help'))


    @property 
    def invite_link(self):
        # https://discordapp.com/oauth2/authorize?client_id=468281173072805889&scope=bot&permissions=35840&guild_id=208895639164026880
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
        return self.invite_link


    def invite_link_to_guild(self, guild_id:int):
        return self.invite_link + f'&guild_id={guild_id}'


    async def startup(self):
        '''
        Resets and fills the FamilyTreeMember cache with objects
        '''

        # Remove caches
        logger.debug("Clearing caches")
        FamilyTreeMember.all_users = {}
        CustomisedTreeUser.all_users.clear()
        self.blacklisted_guilds.clear() 
        self.guild_prefixes.clear() 
        self.dbl_votes.clear() 
        self.blocked_users.clear() 

        # Pick up the blacklisted guilds from the db
        async with self.database() as db:
            blacklisted = await db('SELECT * FROM blacklisted_guilds')
        logger.debug(f"Caching {len(blacklisted)} blacklisted guilds")
        self.blacklisted_guilds = [i['guild_id'] for i in blacklisted]

        # Pick up the blocked users
        async with self.database() as db:
            blocked = await db('SELECT * FROM blocked_user')
        logger.debug(f"Caching {len(blocked)} blocked users")
        for user in blocked:
            x = self.blocked_users.get(user['user_id'], list())
            x.append(user['blocked_user_id'])
            self.blocked_users[user['user_id']] = x

        # Grab the command prefixes per guild
        async with self.database() as db:
            settings = await db('SELECT * FROM guild_settings')
        logger.debug(f"Caching {len(settings)} guild settings")
        for guild_setting in settings:
            self.guild_prefixes[guild_setting['guild_id']] = guild_setting['prefix']

        # Grab the last vote times of each user 
        async with self.database() as db:
            votes = await db('SELECT * FROM dbl_votes')
        logger.debug(f"Caching {len(votes)} DBL votes")
        for v in votes:
            self.dbl_votes[v['user_id']] = v['timestamp']

        # Wait for the bot to cache users before continuing
        logger.debug("Waiting until ready before completing startup method.")
        await self.wait_until_ready()

        # Get family data from database
        async with self.database() as db:
            partnerships = await db('SELECT * FROM marriages')
            parents = await db('SELECT * FROM parents')
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

        # And update DBL
        await self.post_guild_count()        
        
        
    async def on_message(self, message):
        ctx = await self.get_context(message, cls=CustomContext)
        await self.invoke(ctx)


    def get_tree_guild_id(self, guild_id:int):
        '''Gives you the ID of the guild the family should be processed on''' 
        
        return guild_id if guild_id in self.server_specific_families else 0

    
    async def get_name(self, user_id):
        user = self.get_user(user_id) or self.shallow_users.get(user_id)
        if user and isinstance(user, User):
            return str(user)
        elif user:
            if user[1] > 0:
                self.shallow_users[user_id] = [user[0], user[1] - 1] 
                return str(user[0])
        name = await self.fetch_user(user_id)
        self.shallow_users[user_id] = [name, 20]
        return str(name)


    def get_uptime(self) -> float:
        '''
        Gets the uptime of the bot in seconds
        '''

        return (dt.now() - self.startup_time).total_seconds()


    def get_extensions(self) -> list:
        '''
        Gets the filenames of all the loadable cogs
        '''

        ext = glob('cogs/[!_]*.py')
        # rand = glob('cogs/utils/random_text/[!_]*.py')
        rand = []
        extensions = [i.replace('\\', '.').replace('/', '.')[:-3] for i in ext + rand]
        logger.debug("Getting all extensions: " + str(extensions))
        return extensions


    def load_all_extensions(self):
        '''
        Loads all extensions from .get_extensions()
        '''

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
        '''
        Sets the default presence of the bot as appears in the config file
        '''
        
        # Update presence
        presence_text = self.config['presence_text']
        if not shard_id:
            logger.debug("Setting default bot presence globally")
            if self.shard_count > 1:
                for i in range(self.shard_count):
                    game = Game(f"{presence_text} (shard {i})")
                    await self.change_presence(activity=game, shard_id=i)
            else:
                game = Game(presence_text)
                await self.change_presence(activity=game)
        else:
            logger.debug(f"Setting default bot presence for shard {shard_id}")   
            game = Game(f"{presence_text} (shard {i})")
            await self.change_presence(activity=game, shard_id=i)     


    async def post_guild_count(self):
        '''
        The loop of uploading the guild count to the DBL server
        '''

        # Only post if there's actually a DBL token set
        if not self.config.get('dbl_token'):
            return
        if not self.shard_id in [0, None]:
            return
        logger.debug("Sending POST request to DBL")

        url = f'https://discordbots.org/api/bots/{self.user.id}/stats'
        json = {
            'server_count': len(self.guilds),
            'shard_count': self.shard_count,
            'shard_id': 0,
        }
        headers = {
            'Authorization': self.config['dbl_token']
        }
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
        logger.debug("Reloading config")
        with open(self.config_file) as a:
            self.config = load(a)


    def run(self, *args, **kwargs):
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
