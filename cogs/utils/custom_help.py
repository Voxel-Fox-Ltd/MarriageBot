from discord.ext.commands import HelpFormatter


class CustomHelp(HelpFormatter):
    '''Custom help command, add vote page to bottom'''
    
    def __init__(self):
        super().__init__()

    async def format_help_for(self, context, command_or_bot):
        '''Same as default apart from the added vote page at the bottom'''

        self.context = context
        self.command = command_or_bot
        v = await self.format()
        v[-1] += '\nAdd a vote on DBL (<https://discordbots.org/bot/468281173072805889/vote>) or support me on Patreon (<https://patreon.com/CallumBartlett>) c:'
        return v
