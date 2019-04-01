from argparse import ArgumentParser
from ssl import SSLContext
import logging

from aiohttp.web import Application, AppRunner, TCPSite
from discord import Game, Status
from discord.ext.commands import when_mentioned_or

from cogs.utils.custom_bot import CustomBot
from website.api import routes as api_routes

logging.basicConfig(level=logging.WARNING)
# logger = logging.getLogger('discord')
# logger.setLevel(logging.DEBUG)
logger = logging.getLogger('marriagebot')


# Parse arguments
parser = ArgumentParser()
parser.add_argument("config_file", help="The configuration for the bot.")
parser.add_argument("--noserver", action="store_true", default=False, help="Starts the bot with no web server.")
parser.add_argument("--nossl", action="store_true", default=False, help="Starts the bot with no SSL web server.")
parser.add_argument("--host", type=str, default='0.0.0.0', help="The host IP to run the webserver on.")
parser.add_argument("--port", type=int, default=80, help="The port to run the webserver on.")
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
app = Application(loop=bot.loop)
app.add_routes(api_routes)
app['bot'] = bot


@bot.event
async def on_ready():
    '''
    Runs when the bot is connected to the Discord servers
    Method is used to set the presence and load cogs
    '''

    logger.info('Bot connected:')
    logger.info(f'\t{bot.user}')
    logger.info(f'\t{bot.user.id}')

    logger.info('Loading extensions... ')
    bot.load_all_extensions()
    
    logger.info("Setting activity to default")
    await bot.set_default_presence()
    logger.info('Bot loaded.')


if __name__ == '__main__':
    '''
    Starts the bot (and webserver if specified) and runs forever
    '''

    loop = bot.loop 
    # loop.set_debug(True)

    logger.info("Starting bot...")
    bot.loop.create_task(bot.start_all())

    # Start the server unless I said otherwise
    if not args.noserver:

        # HTTP server
        logger.info("Starting server...")
        application = AppRunner(app)
        loop.run_until_complete(application.setup())
        webserver = TCPSite(application, host=args.host, port=args.port)

        # SSL server
        ssl_webserver = None
        try:
            if not args.nossl:
                ssl_context = SSLContext()
                ssl_context.load_cert_chain(**bot.config['ssl_context'])
                ssl_webserver = TCPSite(application, host=args.host, port=443, ssl_context=ssl_context)
        except Exception as e:
            ssl_webserver = None 
            logger.exception("Could not make SSL webserver")

        # Start servers
        loop.run_until_complete(webserver.start())
        logger.info(f"Server started - http://{args.host}:{args.port}/")
        if ssl_webserver:
            loop.run_until_complete(ssl_webserver.start())
            logger.info(f"Server started - http://{args.host}:443/")

        # Store stuff in the bot for later
        bot.webserver = webserver
        bot.ssl_webserver = ssl_webserver

    # This is the forever loop
    try:
        loop.run_forever()
    except (Exception, KeyboardInterrupt): 
        pass
    finally:
        loop.run_until_complete(bot.logout())

        # Close webservers
        if bot.webserver:
            loop.run_until_complete(bot.webserver.cleanup())
        if bot.ssl_webserver:
            loop.run_until_complete(bot.ssl_webserver.cleanup())

    # Close the asyncio loop
    loop.close()
