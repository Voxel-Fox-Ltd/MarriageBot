from glob import glob
from cogs.utils.custom_bot import CustomBot


bot = CustomBot(
    command_prefix=['m!', '<@468281173072805889> ', '<@!468281173072805889> '], 
    config_file='config/config.json'
    )


def get_extensions() -> list:
    '''
    Gets the filenames of all the loadable cogs
    '''

    ext = glob('cogs/[!_]*.py')
    return [i.replace('\\', '.').replace('/', '.')[:-3] for i in ext]


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

    print('\nEverything loaded.')


print('Starting...')
bot.run_all()  # Custom run
