from discord.ext.commands import HelpFormatter


class CustomHelp(HelpFormatter):
    '''Custom help command, add vote page to bottom'''
    
    def __init__(self):
        super().__init__()

    async def format_help_for(self, context, command_or_bot):
        '''Same as default apart from the added vote page at the bottom'''

        self.context = context
        self.command = command_or_bot
        bot = context.bot
        dbl_link = bot.config['dbl_vainity'] or bot.user.id
        v = await self.format()
        if bot.config.get('dbl_token') and bot.config.get('patreon'):
            extra_text = f'Add a vote on DBL (<https://discordbots.org/bot/{dbl_link}/vote>) or support me on Patreon (<{bot.config["patreon"]}>) c:'
        elif bot.config.get('dbl_token'):
            extra_text = f'Add a vote on DBL (<https://discordbots.org/bot/{dbl_link}/vote>) c:'
        elif bot.config.get('patreon'):
            extra_text = f'Support me on Patreon (<{bot.config["patreon"]}>) c:'
        else:
            extra_text = ''
        v[-1] += extra_text
        return v
