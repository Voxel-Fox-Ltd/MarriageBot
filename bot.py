from argparse import ArgumentParser
from warnings import filterwarnings
import logging

import discord

from cogs.utils.custom_bot import CustomBot
from cogs.utils.database import DatabaseConnection


# Set up loggers
logging.basicConfig(format='%(name)s:%(levelname)s: %(message)s')

# Filter warnings
filterwarnings('ignore', category=RuntimeWarning)

# Parse arguments
parser = ArgumentParser()
parser.add_argument("config_file", help="The configuration for the bot.")
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
    help="The amount of shards that the bot should be using."
)
parser.add_argument("--loglevel", default="INFO")
args = parser.parse_args()

# Create bot object
shard_ids = None if args.shardcount == None else list(range(args.min, args.max+1))
if args.shardcount == None and (args.min or args.max):
    raise Exception("You set a min/max shard but no shard count.")
    exit(1) 
bot = CustomBot(
    config_file=args.config_file,
    activity=discord.Game(name="Reconnecting..."),
    status=discord.Status.dnd,
    case_insensitive=True,
    shard_count=args.shardcount,
    shard_ids=shard_ids,
    shard_id=args.min,
)

# Set up our loggers
logger = bot.logger
log_level = getattr(logging, args.loglevel.upper(), None)
if log_level is None:
    raise Exception("Invalid log level provided")
logger.setLevel(log_level)
logging.getLogger("discord").setLevel(logging.INFO)


@bot.event
async def on_ready():
    """Run when the bot connects to Discord properly
    Sets presence to default and not a lot else"""

    logger.info('Bot connected:')
    logger.info(f'\t{bot.user}')
    logger.info(f'\t{bot.user.id}')
    
    logger.info("Setting activity to default")
    await bot.set_default_presence()
    logger.info('Bot loaded.')


if __name__ == '__main__':
    """Starts the bot, connects the database, runs the async loop forever"""

    # Grab the event loop
    loop = bot.loop 

    # Connect the database
    logger.info("Creating database pool")
    try:
        loop.run_until_complete(DatabaseConnection.create_pool(bot.config['database']))
    except Exception as e:
        logger.critical("Error creating database pool")
        raise e

    # Load the bot's extensions
    logger.info('Loading extensions... ')
    bot.load_all_extensions()

    # Run the bot
    try:
        logger.info("Running bot")
        bot.run()
    except KeyboardInterrupt: 
        pass

    # We're now done running the bot, time to clean up and close
    logger.info("Closing database pool")
    loop.run_until_complete(DatabaseConnection.pool.close())
    logger.info("Closing asyncio loop")
    loop.close()
