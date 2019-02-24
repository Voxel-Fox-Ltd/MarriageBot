from datetime import datetime as dt
from json import load
from importlib import import_module
from asyncio import sleep, create_subprocess_exec
from glob import glob
from re import compile

from aiohttp import ClientSession
from aiohttp.web import Application, AppRunner, TCPSite
from discord import Game, Message
from discord.ext.commands import AutoShardedBot, when_mentioned_or, cooldown
from discord.ext.commands.cooldowns import BucketType

from cogs.utils.database import DatabaseConnection
from cogs.utils.family_tree.family_tree_member import FamilyTreeMember
from cogs.utils.customised_tree_user import CustomisedTreeUser
from cogs.utils.removal_dict import RemovalDict


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

        # Add webserver stuff so I can come back to it later
        self.web_runner = None

        # Allow database connections like this
        self.database = DatabaseConnection
        self.database.config = self.config['database']

        # Store the startup method so I can see if it completed successfully
        self.startup_time = dt.now()
        self.startup_method = self.loop.create_task(self.startup())
        self.deletion_method = self.loop.create_task(self.delete_loop())

        # Add a cache for proposing users
        self.proposal_cache = RemovalDict()

        # Add a list of blacklisted guilds
        self.blacklisted_guilds = []

        # Dictionary of custom prefixes
        self.guild_prefixes = {}  # guild_id: prefix
        
        # Add a cooldown to help
        cooldown(1, 5, BucketType.user)(self.get_command('help'))


    async def startup(self):
        '''
        Resets and fills the FamilyTreeMember cache with objects
        '''

        # Cache all users for easier tree generation
        FamilyTreeMember.all_users = {None: None}

        # Get all from database
        async with self.database() as db:
            partnerships = await db('SELECT * FROM marriages WHERE valid=TRUE')
            parents = await db('SELECT * FROM parents')
            customisations = await db('SELECT * FROM customisation')
        
        # Cache all into objects
        for i in partnerships:
            FamilyTreeMember(discord_id=i['user_id'], children=[], parent_id=None, partner_id=i['partner_id'])
        for i in parents:
            parent = FamilyTreeMember.get(i['parent_id'])
            parent._children.append(i['child_id'])
            child = FamilyTreeMember.get(i['child_id'])
            child._parent = i['parent_id']
        for i in customisations:
            CustomisedTreeUser(**i)

        # Pick up the blacklisted guilds from the db
        async with self.database() as db:
            blacklisted = await db('SELECT * FROM blacklisted_guilds')
        self.blacklisted_guilds = [i['guild_id'] for i in blacklisted]

        # Now wait for the stuff you need to actually be online for
        await self.wait_until_ready()
        await self.set_default_presence()

        # Grab the command prefixes per guild
        async with self.database() as db:
            settings = await db('SELECT * FROM guild_settings')
        for guild_setting in settings:
            self.guild_prefixes[guild_setting['guild_id']] = guild_setting['prefix']

        # Remove anyone who's empty or who the bot can't reach
        async with self.database() as db:
            for user_id, ftm in FamilyTreeMember.all_users.copy().items():
                if user_id == None or ftm == None:
                    continue
                if self.get_user(user_id) == None:
                    await db.destroy(user_id)
                    ftm.destroy()

        # And update DBL
        await self.post_guild_count()


    def get_uptime(self):
        '''
        Gets the uptime of the bot
        '''

        return (dt.now() - self.startup_time).total_seconds()


    def get_extensions(self) -> list:
        '''
        Gets the filenames of all the loadable cogs
        '''

        ext = glob('cogs/[!_]*.py')
        rand = glob('cogs/utils/random_text/[!_]*.py')
        return [i.replace('\\', '.').replace('/', '.')[:-3] for i in ext + rand]


    def load_all_extensions(self):
        '''
        Loads all extensions from .get_extensions()
        '''

        print('Loading extensions... ')
        for i in self.get_extensions():
            self.unload_extension(i)
        for i in self.get_extensions():
            print('\t' + i + '... ', end='')
            try:
                self.load_extension(i)
                print('success')
            except Exception as e:
                print(e)


    async def set_default_presence(self):
        '''
        Sets the default presence of the bot as appears in the config file
        '''
        
        # Update presence
        presence_text = self.config['presence_text']
        if self.shard_count > 1:
            for i in range(self.shard_count):
                game = Game(f"{presence_text} (shard {i})")
                await self.change_presence(activity=game, shard_id=i)
        else:
            game = Game(presence_text)
            await self.change_presence(activity=game)


    async def post_guild_count(self):
        '''
        The loop of uploading the guild count to the DBL server
        '''

        # Only post if there's actually a DBL token set
        if not self.config.get('dbl_token'):
            return

        async with ClientSession(loop=self.loop) as session:
            url = f'https://discordbots.org/api/bots/{self.user.id}/stats'
            json = {
                'server_count': len(self.guilds),
                'shard_count': self.shard_count,
                'shard_id': 0,
            }
            headers = {
                'Authorization': self.config['dbl_token']
            }
            async with session.post(url, json=json, headers=headers) as r:
                pass


    async def delete_loop(self):
        '''
        A loop that runs every hour, deletes all files in the tree storage directory
        '''

        await self.wait_until_ready()
        while not self.is_closed: 
            await create_subprocess_exec('rm', f'{self.config["tree_file_location"]}/*', loop=self.bot.loop)
            await sleep(60*60)


    async def destroy(self, user_id:int):
        '''
        Removes a user ID from the database and cache
        '''

        async with self.database() as db:
            await db.destroy(user_id)
        FamilyTreeMember.get(user_id).destroy()


    def reload_config(self):
        with open(self.config_file) as a:
            self.config = load(a)


    def run_all(self):
        self.run(self.config['token'])


    async def start_all(self):
        await self.start(self.config['token'])


    async def logout(self):
        '''
        An override of the default logout that also closes the webserver
        '''

        try:
            await self.web_runner.cleanup()
        except Exception as e:
            print("Error with closing previous server: ", e)
        await self.close()


    async def restart_webserver(self, *imports):
        '''
        Stops the current running webserver and starts a new one

        Args:
            *imports: str
                A list of modules to import that contain a "routes" attribute
        '''

        try:
            await self.web_runner.cleanup()
        except Exception as e:
            print("Error with closing previous server: ", e)

        # Make and link all the relevant options
        app = Application(loop=self.loop)
        for i in imports:
            x = import_module(i)
            app.add_routes(x.routes)
        app['bot'] = self

        # Run the site
        self.web_runner = AppRunner(app)
        await self.web_runner.setup()
        site = TCPSite(self.web_runner, self.commandline_args.host, self.commandline_args.port)
        await site.start()

        print(f"Server started: http://{self.commandline_args.host}:{self.commandline_args.port}/")
