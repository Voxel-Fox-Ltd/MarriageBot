import os
import argparse
import secrets
import ssl
import warnings
import logging

from aiohttp.web import Application, AppRunner, TCPSite
import discord
import aiohttp_jinja2 as jinja
import aiohttp_session as session
from aiohttp_session.cookie_storage import EncryptedCookieStorage as ECS
from jinja2 import FileSystemLoader

from cogs.utils.custom_bot import CustomBot
from cogs.utils.database import DatabaseConnection
from cogs.utils.redis import RedisConnection
from website.api import routes as api_routes
from website.frontend import routes as frontend_routes

# Set up a basic logger for us to use for a lil bit
logging.basicConfig(format='%(name)s:%(levelname)s: %(message)s')
logger = logging.getLogger(os.getcwd().split(os.sep)[-1])

# Filter warnings
warnings.filterwarnings('ignore', category=RuntimeWarning)

# Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("config_file", help="The configuration for the bot")
parser.add_argument(
    "--min", type=int, default=None,
    help="The minimum shard ID that this instance will run with (inclusive)"
)
parser.add_argument(
    "--max", type=int, default=None,
    help="The maximum shard ID that this instance will run with (inclusive)"
)
parser.add_argument(
    "--shardcount", type=int, default=None,
    help="The amount of shards that the bot should be using"
)
parser.add_argument(
    "--noserver", action="store_true", default=False,
    help="Starts the bot with no web server"
)
parser.add_argument(
    "--nossl", action="store_true", default=False,
    help="Starts the bot with no SSL web server"
)
parser.add_argument(
    "--host", type=str, default='0.0.0.0',
    help="The host IP to run the webserver on"
)
parser.add_argument(
    "--port", type=int, default=8080,
    help="The port to run the webserver on"
)
parser.add_argument(
    "--sslport", type=int, default=8443,
    help="The port to run the SSL webserver on"
)
parser.add_argument(
    "--loglevel", default="INFO",
    help="Logging level for the bot - probably most useful is INFO and DEBUG"
)
args = parser.parse_args()

# Make sure the sharding info provided is correctish
if args.shardcount is None:
    shard_ids = None
else:
    shard_ids = list(range(args.min, args.max+1))
if args.shardcount is None and (args.min or args.max):
    logger.critical("You set a min/max shard handler but no shard count")
    exit(1)

# Okay cool make the bot object
bot = CustomBot(
    config_file=args.config_file,
    activity=discord.Game(name="Reconnecting..."),
    status=discord.Status.dnd,
    case_insensitive=True,
    shard_count=args.shardcount,
    shard_ids=shard_ids,
    shard_id=args.min,
    max_messages=100,  # The lowest amount that we can actually cache
    fetch_offline_members=False,
    logger=logger.getChild('bot')
)

# Set up out loggers
log_level = getattr(logging, args.loglevel.upper(), None)
if log_level is None:
    raise Exception("Invalid log level provided")
    exit(1)
logger.setLevel(log_level)

# Create website object - this is used for the webhook handler
app = Application(loop=bot.loop, debug=True)
app.add_routes(api_routes)
app.router.add_static('/static', os.getcwd() + '/website/static')
app['bot'] = bot
app['static_root_url'] = '/static'
jinja.setup(app, loader=FileSystemLoader(os.getcwd() + '/website/templates'))
session.setup(app, ECS(secrets.token_bytes(32)))


if __name__ == '__main__':
    """Start the bot, database pool, redis pool, and webserver,
    and run the loop forever"""

    # Grab the event loop
    loop = bot.loop

    # Connect the database
    logger.info("Creating database pool")
    try:
        db_connect = DatabaseConnection.create_pool(bot.config['database'])
        loop.run_until_complete(db_connect)
    except KeyError as e:
        logger.critical("KeyError creating database pool - "
                        "is there a 'database' object in the config?")
        if logger.level > logging.DEBUG:
            exit(1)
        else:
            raise e
    except ConnectionRefusedError as e:
        logger.critical("ConnectionRefusedError creating database pool - "
                        "did you set the right information in the config, "
                        "and is the database running?")
        if logger.level > logging.DEBUG:
            exit(1)
        else:
            raise e
    except Exception as e:
        logger.critical("Error creating database pool")
        raise e
    logger.info("Created database pool successfully")

    # Connect the redis
    logger.info("Creating redis pool")
    try:
        re_connect = RedisConnection.create_pool(bot.config['redis'])
        loop.run_until_complete(re_connect)
    except KeyError as e:
        logger.critical("KeyError creating redis pool - "
                        "is there a 'redis' object in the config?")
        if logger.level > logging.DEBUG:
            exit(1)
        else:
            raise e
    except ConnectionRefusedError as e:
        logger.critical("ConnectionRefusedError creating redis pool - "
                        "did you set the right information in the config, "
                        "and is the database running?")
        if logger.level > logging.DEBUG:
            exit(1)
        else:
            raise e
    except Exception as e:
        logger.critical("Error creating redis pool")
        raise e
    logger.info("Created redis pool successfully")

    # Load the bot's extensions
    logger.info('Loading extensions')
    bot.load_all_extensions()

    # Start the webserver(s)
    webserver = None
    ssl_webserver = None
    if not args.noserver:

        # HTTP server
        logger.info("Creating webserver")
        application = AppRunner(app)
        loop.run_until_complete(application.setup())
        webserver = TCPSite(application, host=args.host, port=args.port)
        logger.info("Created webserver successfully")

        # SSL server
        try:
            if not args.nossl:
                logger.info("Creating SSL webserver")
                ssl_context = ssl.SSLContext()
                ssl_context.load_cert_chain(**bot.config['ssl_context'])
                ssl_webserver = TCPSite(
                    application, host=args.host,
                    port=args.sslport, ssl_context=ssl_context
                )
                logger.info("Created SSL webserver successfully")
        except Exception as e:
            ssl_webserver = None
            logger.exception("Could not make SSL webserver - "
                             "continuing without")

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
        logger.info("Webserver closed")
    logger.info("Closing database pool")
    loop.run_until_complete(DatabaseConnection.pool.close())
    logger.info("Database pool closed")
    logger.info("Closing redis pool")
    loop.run_until_complete(RedisConnection.pool.close())
    logger.info("Redis pool closed")
    logger.info("Closing asyncio loop")
    loop.close()
    logger.info("Asyncio loop closed")
