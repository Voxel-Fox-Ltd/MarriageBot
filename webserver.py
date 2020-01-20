import asyncio
import os
import argparse
import warnings
import logging

from aiohttp.web import Application, AppRunner, TCPSite
from aiohttp_jinja2 import setup as jinja_setup
from aiohttp_session import setup as session_setup, SimpleCookieStorage
from aiohttp_session.cookie_storage import EncryptedCookieStorage as ECS
from jinja2 import FileSystemLoader
import toml

from cogs import utils
import website


# Set up loggers
logging.getLogger().setLevel(logging.INFO)
logging.basicConfig(format='%(name)s:%(levelname)s: %(message)s')
logger = logging.getLogger('website')
logger.setLevel(logging.INFO)

# Filter warnings
warnings.filterwarnings('ignore', category=RuntimeWarning)

# Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("config_file", help="The configuration for the webserver.")
parser.add_argument("--host", type=str, default='0.0.0.0', help="The host IP to run the webserver on.")
parser.add_argument("--port", type=int, default=8080, help="The port to run the webserver on.")
args = parser.parse_args()

# Read config
with open(args.config_file) as a:
    config = toml.load(a)

# Create website object - don't start based on argv
app = Application(loop=asyncio.get_event_loop())
app['static_root_url'] = '/static'
session_setup(app, ECS(os.urandom(32), max_age=1000000))  # Encrypted cookies
# session_setup(app, SimpleCookieStorage(max_age=1000000))  # Simple cookies DEBUG ONLY
jinja_setup(app, loader=FileSystemLoader(os.getcwd() + '/website/templates'))
app.router.add_routes(website.frontend_routes)
app.router.add_routes(website.backend_routes)
app.router.add_static('/static', os.getcwd() + '/website/static', append_version=True)

# Add our connections
app['database'] = utils.DatabaseConnection
utils.DatabaseConnection.logger = logger.getChild("db")

# Add our configs
app['config'] = config

# Add our bots
app['bot'] = utils.CustomBot(config_file=args.config_file, logger=logger.getChild("bot"))


if __name__ == '__main__':
    """Starts the bot (and webserver if specified) and runs forever"""

    loop = app.loop

    # Connect the bot
    logger.info("Logging in bot")
    loop.run_until_complete(app['bot'].login(app['config']['token']))

    # Connect the database
    logger.info("Creating database pool")
    loop.run_until_complete(utils.DatabaseConnection.create_pool(app['config']['database']))

    # HTTP server
    logger.info("Creating webserver...")
    application = AppRunner(app)
    loop.run_until_complete(application.setup())
    webserver = TCPSite(application, host=args.host, port=args.port)

    # Start server
    loop.run_until_complete(webserver.start())
    logger.info(f"Server started - http://{args.host}:{args.port}/")

    # This is the forever loop
    try:
        logger.info("Running webserver")
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    # Clean up our shit
    logger.info("Closing webserver")
    loop.run_until_complete(application.cleanup())
    logger.info("Closing database pool")
    loop.run_until_complete(utils.DatabaseConnection.pool.close())
    logger.info("Closing bot")
    loop.run_until_complete(app['bot'].close())
    logger.info("Closing asyncio loop")
    loop.close()
