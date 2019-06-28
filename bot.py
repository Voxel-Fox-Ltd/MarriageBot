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
from cogs.utils.redis import RedisConnection
from website.api import routes as api_routes
from website.frontend import routes as frontend_routes

# Set up loggers
logging.basicConfig(format='%(asctime)s:%(name)s:%(levelname)s: %(message)s')
root = logging.getLogger()
root.setLevel(logging.INFO)
logging.getLogger('marriagebot.db').setLevel(logging.INFO)
logging.getLogger('marriagebot.redis').setLevel(logging.INFO)
logger = logging.getLogger('marriagebot')
logger.setLevel(logging.DEBUG)

# Filter warnings
filterwarnings('ignore', category=RuntimeWarning)

# Parse arguments
parser = ArgumentParser()
parser.add_argument("config_file", help="The configuration for the bot.")
parser.add_argument("--min", type=int, default=None, help="The minimum shard ID that this instance will run with (inclusive)")
parser.add_argument("--max", type=int, default=None, help="The maximum shard ID that this instance will run with (inclusive)")
parser.add_argument("--shardcount", type=int, default=None, help="The amount of shards that the bot should be using.")
parser.add_argument("--noserver", action="store_true", default=False, help="Starts the bot with no web server.")
parser.add_argument("--nossl", action="store_true", default=False, help="Starts the bot with no SSL web server.")
parser.add_argument("--host", type=str, default='0.0.0.0', help="The host IP to run the webserver on.")
parser.add_argument("--port", type=int, default=8080, help="The port to run the webserver on.")
parser.add_argument("--sslport", type=int, default=8443, help="The port to run the SSL webserver on.")
args = parser.parse_args()

# Create bot object
shard_ids = None if args.shardcount == None else list(range(args.min, args.max+1))
if args.shardcount == None and (args.min or args.max):
    raise Exception("You set a min/max shard handler but no shard count")
bot = CustomBot(
    config_file=args.config_file,
    activity=Game(name="Reconnecting..."),
    status=Status.dnd,
    case_insensitive=True,
    shard_count=args.shardcount,
    shard_ids=shard_ids,
    shard_id=args.min,
    max_messages=100,
    fetch_offline_members=False,
)

# Create website object - this is used for the webhook handler
app = Application(loop=bot.loop, debug=True)
app.add_routes(api_routes)
app.router.add_static('/static', getcwd() + '/website/static')
app['bot'] = bot
app['static_root_url'] = '/static'
jinja_setup(app, loader=FileSystemLoader(getcwd() + '/website/templates'))
session_setup(app, ECS(token_bytes(32)))


if __name__ == '__main__':
    '''
    Starts the bot (and webserver if specified) and runs forever
    '''

    # Grab the event loop
    loop = bot.loop 

    # Connect the database
    logger.info("Creating database pool")
    try:
        loop.run_until_complete(DatabaseConnection.create_pool(bot.config['database']))
    except Exception as e:
        logger.error("Error creating database pool")
        raise e

    # Connect the redis
    logger.info("Creating redis pool")
    try:
        loop.run_until_complete(RedisConnection.create_pool(bot.config['redis']))
    except Exception as e:
        logger.error("Error creating Redis pool")

    # Load the bot's extensions
    logger.info('Loading extensions... ')
    bot.load_all_extensions()

    # Start the webserver(s)
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

    # Run the bot
    try:
        logger.info("Running bot")
        bot.run()
    except KeyboardInterrupt: 
        pass

    # We're now done running the bot, time to clean up and close
    if webserver:
        logger.info("Closing webserver")
        loop.run_until_complete(application.cleanup())
    logger.info("Closing database pool")
    loop.run_until_complete(DatabaseConnection.pool.close())
    logger.info("Closing redis pool")
    loop.run_until_complete(RedisConnection.pool.close())
    logger.info("Closing asyncio loop")
    loop.close()
