from argparse import ArgumentParser
from glob import glob
from aiohttp.web import run_app, Application
from discord import Game, Status
from discord.ext.commands import when_mentioned_or
from cogs.utils.custom_bot import CustomBot
from cogs.utils.custom_help import CustomHelp
from website.index import routes


# Parse arguments
parser = ArgumentParser()
parser.add_argument(
    "config_file", 
    help="The configuration for the bot."
)
parser.add_argument(
    "-n", "--noserver", 
    action="store_true", 
    default=False, 
    help="Starts the bot with no web server."
)
parser.add_argument(
    "-p", "--port", 
    type=int,
    default=8080, 
    help="The port to run the webserver on."
)
args = parser.parse_args()


# Create bot object
bot = CustomBot(
    config_file=args.config_file,
    formatter=CustomHelp(),
    activity=Game(name="Restarting..."),
    status=Status.dnd
)


# Create website
app = Application(loop=bot.loop)
app.add_routes(routes)
app['bot'] = bot


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
    # See if inital ones were specified in config
    x = bot.config.get('initial_cogs')
    if x:
        for i in x:
            print('\t' + i + '... ', end='')
            try:
                bot.load_extension(i)
                print('success')
            except Exception as e:
                print(e)
    # They weren't, grab them all
    else:
        for i in get_extensions():
            print('\t' + i + '... ', end='')
            try:
                bot.load_extension(i)
                print('success')
            except Exception as e:
                print(e)

    print('\nEverything loaded.\n')


if __name__ == '__main__':
    print("Starting bot...")
    loop = bot.loop
    bot.loop.create_task(bot.start_all())

    # Run with no server
    if args.noserver:
        try:
            loop.run_forever()
        except Exception: 
            loop.run_until_complete(bot.logout())
        finally:
            loop.close()

    # Run with the server
    else:
        print("Starting server...")
        run_app(app, port=args.port)
