from argparse import ArgumentParser
from ssl import SSLContext

from aiohttp.web import Application, AppRunner, TCPSite
from discord import Game, Status
from discord.ext.commands import when_mentioned_or

from cogs.utils.custom_bot import CustomBot
from website.api import routes as api_routes

import logging
logging.basicConfig(level=logging.WARNING)
# logger = logging.getLogger('discord')
# logger.setLevel(logging.DEBUG)


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
    "-ns", "--nossl", 
    action="store_true", 
    default=False, 
    help="Starts the bot with no SSL web server."
)
parser.add_argument(
    "-i", "--host", 
    type=str,
    default='0.0.0.0', 
    help="The host IP to run the webserver on."
)
parser.add_argument(
    "-p", "--port", 
    type=int,
    default=80, 
    help="The port to run the webserver on."
)
args = parser.parse_args()


# Create bot object
bot = CustomBot(
    config_file=args.config_file,
    activity=Game(name="Restarting..."),
    status=Status.dnd,
    commandline_args=args,
    case_insensitive=True,
)


# Create website
app = Application(loop=bot.loop)
app.add_routes(api_routes)
app['bot'] = bot


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
    bot.load_all_extensions()
    print('Bot loaded.')


if __name__ == '__main__':
    '''
    Starts the bot (and webserver if specified) and runs forever
    '''

    loop = bot.loop 
    # loop.set_debug(True)

    print("Starting bot...")
    bot.loop.create_task(bot.start_all())

    if not args.noserver:
        print("Starting server...")
        web_runner = AppRunner(app)
        loop.run_until_complete(web_runner.setup())
        site = TCPSite(web_runner, host=args.host, port=args.port)
        loop.run_until_complete(site.start())
        print(f"Server started: http://{args.host}:{args.port}/")

        # Start SSL server
        if not args.nossl:
            ssl_context = SSLContext()
            ssl_context.load_cert_chain(**bot.config['ssl_context'])
            ssl_site = TCPSite(web_runner, host=args.host, port=443, ssl_context=ssl_context)
            loop.run_until_complete(ssl_site.start())
            print(f"Server started: http://{args.host}:443/")

        # Store stuff in the bot for later
        bot.web_runner = web_runner

    # This is the forever loop
    try:
        loop.run_forever()
    except (Exception, KeyboardInterrupt): 
        pass
    finally:
        # Logout the bot
        loop.run_until_complete(bot.logout())

        if not args.noserver:
            # Try and gracefully close the server
            try:
                loop.run_until_complete(bot.web_runner.cleanup())
            except Exception as e:
                # Maybe I restarted the server via the bot at runtime
                print(e)

    # Close the loop
    loop.close()
