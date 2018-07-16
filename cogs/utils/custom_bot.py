from json import load
from discord.ext.commands import AutoShardedBot
from cogs.utils.database import DatabaseConnection


class CustomBot(AutoShardedBot):

    def __init__(self, config_file:str='config.json', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._config = None  # See the config property
        self.config_file = config_file
        self.database = DatabaseConnection
        self.database.config = self.config['database']


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
    

