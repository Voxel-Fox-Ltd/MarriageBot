from json import load
from asyncio import sleep
from aiohttp import ClientSession
from discord import Game
from discord.ext.commands import AutoShardedBot
from cogs.utils.database import DatabaseConnection
from cogs.utils.family_tree.family_tree_member import FamilyTreeMember


class CustomBot(AutoShardedBot):

    def __init__(self, config_file:str='config.json', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = None
        self.config_file = config_file
        self.reload_config()
        self.database = DatabaseConnection
        self.database.config = self.config['database']

        self.startup_method = self.loop.create_task(self.startup())
        self.presence_loop = self.loop.create_task(self.presence_loop())

        self.proposal_cache = []


    async def presence_loop(self):
        '''
        A loop of changing the presence for the botto
        '''

        await self.wait_until_ready()
        while not self.is_closed():
            presence_text = self.config['presence_text']
            for string in presence_text:
                game = Game(string)
                await self.change_presence(activity=game)
                await sleep(60)


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
        
        # Cache all into FamilyTreeMember objects
        for i in partnerships:
            FamilyTreeMember(discord_id=i['user_id'], children=[], parent_id=None, partner_id=i['partner_id'])
        for i in parents:
            parent = FamilyTreeMember.get(i['parent_id'])
            parent.children.append(i['child_id'])
            child = FamilyTreeMember.get(i['child_id'])
            child.parent = i['parent_id']

        # Remove anyone who's empty or who the bot can't reach
        await self.wait_until_ready()  # So I can use get_user
        async with self.database() as db:
            for user_id, ftm in FamilyTreeMember.all_users.copy().items():
                if user_id == None or ftm == None:
                    continue
                if self.get_user(user_id) == None:
                    await db.destroy(user_id)
                    ftm.destroy()

        # And update DBL
        await self.post_guild_count()


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
            }
            headers = {
                'Authorization': self.config['dbl_token']
            }
            async with session.post(url, json=json, headers=headers) as r:
                pass


    def reload_config(self):
        try:
            with open(self.config_file) as a:
                self.config = load(a)
        except Exception as e:
            pass


    def run_all(self):
        self.run(self.config['token'])
    

