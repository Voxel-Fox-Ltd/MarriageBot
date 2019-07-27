from asyncio import get_event_loop
from os import getcwd
from argparse import ArgumentParser
from secrets import token_bytes
from ssl import SSLContext
from warnings import filterwarnings
import logging

from aiohttp.web import Application, AppRunner, TCPSite, middleware, HTTPFound
from discord import Game, Status, Client
from discord.ext.commands import when_mentioned_or
from aiohttp_jinja2 import template, setup as jinja_setup
from aiohttp_session import setup as session_setup, SimpleCookieStorage
from aiohttp_session.cookie_storage import EncryptedCookieStorage as ECS
from aiohttp_session.redis_storage import RedisStorage
from jinja2 import FileSystemLoader
from ujson import load

from cogs.utils.database import DatabaseConnection
from cogs.utils.redis import RedisConnection
from website.api import routes as api_routes
from website.frontend import routes as frontend_routes


# Set up loggers
logging.getLogger().setLevel(logging.DEBUG)
logging.basicConfig(format='%(name)s:%(levelname)s: %(message)s')
logger = logging.getLogger('marriagebot.web')
logger.setLevel(logging.DEBUG)


# Filter warnings
filterwarnings('ignore', category=RuntimeWarning)


# Parse arguments
parser = ArgumentParser()
parser.add_argument("config_file", help="The configuration for the bot.")
parser.add_argument("--nossl", action="store_true", default=False, help="Starts the bot with no SSL web server.")
parser.add_argument("--host", type=str, default='0.0.0.0', help="The host IP to run the webserver on.")
parser.add_argument("--port", type=int, default=8080, help="The port to run the webserver on.")
parser.add_argument("--sslport", type=int, default=8443, help="The port to run the SSL webserver on.")
args = parser.parse_args()


# Read config
with open(args.config_file) as a:
    config = load(a)


# Make the SSL redirect
@middleware
async def ssl_redirect(request, handler):
    if request.url.scheme == 'http':
        url = str(request.url).replace('http://', 'https://', 1)
        return HTTPFound(location=url)
    return await handler(request)


# Create website object - don't start based on argv
app = Application(loop=get_event_loop(), debug=False, middlewares=[ssl_redirect])
app.add_routes(frontend_routes)
app.router.add_static('/static', getcwd() + '/website/static')
app.router.add_static('/trees', config['tree_file_location'])
app['static_root_url'] = '/static'
app['database'] = DatabaseConnection
app['redis'] = RedisConnection
app['config'] = config
app['bot'] = Client()
jinja_setup(app, loader=FileSystemLoader(getcwd() + '/website/templates'))


if __name__ == '__main__':
    '''
    Starts the bot (and webserver if specified) and runs forever
    '''

    loop = app.loop 

    logger.info("Creating bot")
    loop.run_until_complete(app['bot'].login(app['config']['token']))

    logger.info("Creating database pool")
    loop.run_until_complete(DatabaseConnection.create_pool(app['config']['database']))

    # Connect the redis
    logger.info("Creating redis pool")
    loop.run_until_complete(RedisConnection.create_pool(app['config']['redis']))

    # Connect redis to middleware
    logger.info("Connecting Redis to app")
    storage = RedisStorage(RedisConnection.pool)
    session_setup(app, storage)

    # Start the server unless I said otherwise
    webserver = None
    ssl_webserver = None

    # HTTP server
    logger.info("Creating webserver...")
    application = AppRunner(app)
    loop.run_until_complete(application.setup())
    webserver = TCPSite(application, host=args.host, port=args.port)

    # SSL server
    try:
        if not args.nossl:
            ssl_context = SSLContext()
            ssl_context.load_cert_chain(**app['config']['ssl_context'])
            ssl_webserver = TCPSite(application, host=args.host, port=args.sslport, ssl_context=ssl_context)
    except Exception as e:
        ssl_webserver = None 
        logger.exception("Could not make SSL webserver")

    # Start servers
    loop.run_until_complete(webserver.start())
    logger.info(f"Server started - http://{args.host}:{args.port}/")
    if ssl_webserver:
        loop.run_until_complete(ssl_webserver.start())
        logger.info(f"Server started - https://{args.host}:{args.sslport}/")

    # This is the forever loop
    try:
        logger.info("Running webserver")
        loop.run_forever()
    except KeyboardInterrupt: 
        pass
    logger.info("Closing webserver")
    loop.run_until_complete(application.cleanup())
    logger.info("Closing database pool")
    loop.run_until_complete(DatabaseConnection.pool.close())
    logger.info("Closing bot")
    loop.run_until_complete(app['bot'].close())
    logger.info("Closing asyncio loop")
    loop.close()
