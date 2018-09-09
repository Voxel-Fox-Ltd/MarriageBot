from glob import glob
from discord import Game, Status
from discord.ext.commands import when_mentioned_or
from cogs.utils.custom_bot import CustomBot
from cogs.utils.custom_help import CustomHelp


bot = CustomBot(
    command_prefix=when_mentioned_or('m!'), 
    config_file='config/config.json',
    formatter=CustomHelp(),
    activity=Game(name="Restarting..."),
    status=Status.dnd
    )


# @bot.check
# async def disable_all(ctx):
#     if str(ctx.author) != 'Caleb#2831': 
#         await ctx.send("This command is temporarily disabled. Apologies.")
#         return False 
#     return True


def get_extensions() -> list:
    '''
    Gets the filenames of all the loadable cogs
    '''

    ext = glob('cogs/[!_]*.py')
    rand = glob('cogs/utils/random_text/[!_]*.py')
    return [i.replace('\\', '.').replace('/', '.')[:-3] for i in ext + rand]


@bot.event
async def on_ready():
    '''
    Runs when the bot is connected to the Discord servers
    Method is used to set the presence and load cogs
    '''

    print('Bot connected:')
    print(f'\t{bot.user}')
    print(f'\t{bot.user.id}')

    print('Loading extensions... ')
    for i in get_extensions():
        print('\t' + i + '... ', end='')
        try:
            bot.load_extension(i)
            print('success')
        except Exception as e:
            print(e)

    print('\nEverything loaded.\n')


print('Starting...')
bot.run_all()  # Custom run
