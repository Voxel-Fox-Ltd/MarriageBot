from os import getcwd
from argparse import ArgumentParser
from secrets import token_bytes
from ssl import SSLContext
from warnings import filterwarnings
from sys import stdout
import logging

from aiohttp.web import Application, AppRunner, TCPSite
from discord import Game, Status
from discord.ext.commands import when_mentioned_or
from aiohttp_jinja2 import template, setup as jinja_setup
from aiohttp_session import setup as session_setup, SimpleCookieStorage
from aiohttp_session.cookie_storage import EncryptedCookieStorage as ECS
from jinja2 import FileSystemLoader

from cogs.utils.custom_bot import CustomBot
from cogs.utils.database import DatabaseConnection
from website.api import routes as api_routes
from website.frontend import routes as frontend_routes

# Set up loggers
logging.basicConfig(format='%(asctime)s:%(name)s:%(levelname)s: %(message)s')
root = logging.getLogger()
root.setLevel(logging.DEBUG)
# logging.getLogger('discord').setLevel(logging.WARNING)
# logging.getLogger('marriagebot.db').setLevel(logging.INFO)
logger = logging.getLogger('marriagebot')
logger.setLevel(logging.DEBUG)

# Filter warnings
filterwarnings('ignore', category=RuntimeWarning)

# Parse arguments
parser = ArgumentParser()
parser.add_argument("config_file", help="The configuration for the bot.")
parser.add_argument("--noserver", action="store_true", default=False, help="Starts the bot with no web server.")
parser.add_argument("--nossl", action="store_true", default=False, help="Starts the bot with no SSL web server.")
parser.add_argument("--host", type=str, default='0.0.0.0', help="The host IP to run the webserver on.")
parser.add_argument("--port", type=int, default=8080, help="The port to run the webserver on.")
parser.add_argument("--sslport", type=int, default=8443, help="The port to run the SSL webserver on.")
args = parser.parse_args()

# Create bot object
bot = CustomBot(
    config_file=args.config_file,
    activity=Game(name="Restarting..."),
    status=Status.dnd,
    commandline_args=args,
    case_insensitive=True,
)

# Create website object - don't start based on argv
app = Application(loop=bot.loop, debug=True)
app.add_routes(api_routes)
app.router.add_static('/static', getcwd() + '/website/static')
app['bot'] = bot
app['static_root_url'] = '/static'
jinja_setup(app, loader=FileSystemLoader(getcwd() + '/website/templates'))
session_setup(app, ECS(token_bytes(32)))


@bot.event
async def on_ready():
    '''
    Runs when the bot is connected to the Discord servers
    Method is used to set the presence and load cogs
    '''

    logger.info('Bot connected:')
    logger.info(f'\t{bot.user}')
    logger.info(f'\t{bot.user.id}')
    
    logger.info("Setting activity to default")
    await bot.set_default_presence()
    logger.info('Bot loaded.')


if __name__ == '__main__':
    '''
    Starts the bot (and webserver if specified) and runs forever
    '''

    loop = bot.loop 
    loop.set_debug(True)


    logger.info("Creating database pool")
    loop.run_until_complete(DatabaseConnection.create_pool(bot.config['database']))

    logger.info('Loading extensions... ')
    bot.load_all_extensions()

    # Start the server unless I said otherwise
    webserver = None
    ssl_webserver = None
    if not args.noserver:

        # HTTP server
        logger.info("Creating webserver...")
        application = AppRunner(app)
        loop.run_until_complete(application.setup())
        webserver = TCPSite(application, host=args.host, port=args.port)

        # SSL server
        try:
            if not args.nossl:
                ssl_context = SSLContext()
                ssl_context.load_cert_chain(**bot.config['ssl_context'])
                ssl_webserver = TCPSite(application, host=args.host, port=args.sslport, ssl_context=ssl_context)
        except Exception as e:
            ssl_webserver = None 
            logger.exception("Could not make SSL webserver")

        # Start servers
        loop.run_until_complete(webserver.start())
        logger.info(f"Server started - http://{args.host}:{args.port}/")
        if ssl_webserver:
            loop.run_until_complete(ssl_webserver.start())
            logger.info(f"Server started - http://{args.host}:{args.sslport}/")

    # This is the forever loop
    try:
        logger.info("Running bot")
        bot.run()
    except KeyboardInterrupt: 
        pass
    if webserver:
        logger.info("Closing webserver")
        loop.run_until_complete(application.cleanup())
    logger.info("Closing database pool")
    loop.run_until_complete(DatabaseConnection.pool.close())
    logger.info("Closing asyncio loop")
    loop.close()
