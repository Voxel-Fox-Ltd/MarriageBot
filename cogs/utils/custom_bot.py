from json import load
from asyncio import sleep
from discord import Game
from discord.ext.commands import AutoShardedBot
from cogs.utils.database import DatabaseConnection


class CustomBot(AutoShardedBot):

    def __init__(self, config_file:str='config.json', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._config = None  # See the config property
        self.config_file = config_file
        self.database = DatabaseConnection
        self.database.config = self.config['database']

        self.presence_loop = self.loop.create_task(self.presence_loop())


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


    @property
    def config(self):
        try:
            with open(self.config_file) as a:
                self._config = load(a)
        except Exception as e:
            pass
        return self._config


    def run_all(self):
        self.run(self.config['token'])
    

