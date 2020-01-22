import argparse
import warnings
import logging
import os
import asyncio
import sys

import discord

from cogs import utils


# Set up loggers
logging.basicConfig(format='%(name)s:%(levelname)s: %(message)s')
logger = logging.getLogger(os.getcwd().split(os.sep)[-1].split()[-1].lower())

# Filter warnings
warnings.filterwarnings('ignore', category=RuntimeWarning)

# Use right event loop
if sys.platform == 'win32':
    loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(loop)

# Parse arguments
def get_program_arguments():
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
        "--loglevel", default="INFO",
        help="Logging level for the bot - probably most useful is INFO and DEBUG"
    )
    parser.add_argument(
        "--loglevel-discord", default="INFO",
        help="Logging level for discord - probably most useful is INFO and DEBUG"
    )
    parser.add_argument(
        "--loglevel-database", default="INFO",
        help="Logging level for database - probably most useful is INFO and DEBUG"
    )
    return parser.parse_args()
args = get_program_arguments()

# Make sure the sharding info provided is correctish
if args.shardcount is None:
    args.shardcount = 1
    args.min = 0
    args.max = 0
shard_ids = list(range(args.min, args.max+1))
if args.shardcount is None and (args.min or args.max):
    logger.critical("You set a min/max shard handler but no shard count")
    exit(1)
if args.shardcount is not None and not (args.min is not None and args.max is not None):
    logger.critical("You set a shardcount but not min/max shards")
    exit(1)

# Okay cool make the bot object
bot = utils.Bot(
    config_file=args.config_file,
    activity=discord.Game(name="Reconnecting..."),
    status=discord.Status.dnd,
    case_insensitive=True,
    shard_count=args.shardcount,
    shard_ids=shard_ids,
    shard_id=args.min,
    max_messages=100,  # The lowest amount that we can actually cache
    logger=logger.getChild('bot'),
)

# Set up out loggers
log_level = getattr(logging, args.loglevel.upper(), None)
if log_level is None:
    logger.critical("An invalid log level was provided")
    exit(1)
logger.setLevel(log_level)
logging.getLogger('discord').setLevel(getattr(logging, args.loglevel_discord.upper(), log_level))
bot.database.logger.setLevel(getattr(logging, args.loglevel_database.upper(), log_level))


@bot.event
async def on_ready():
    """Run when the bot connects to Discord properly
    Sets presence to default and not a lot else"""

    logger.info(f"Bot connected - {bot.user} // {bot.user.id}")
    logger.info("Setting activity to default")
    await bot.set_default_presence()
    logger.info('Bot loaded.')


if __name__ == '__main__':
    """Starts the bot, connects the database, runs the async loop forever"""

    # Grab the event loop
    loop = bot.loop

    # Connect the database connection
    logger.info("Creating database pool")
    try:
        db_connect_task = loop.create_task(utils.DatabaseConnection.create_pool(bot.config['database']))
        loop.run_until_complete(db_connect_task)
    except KeyError as e:
        raise Exception("KeyError creating database pool - is there a 'database' object in the config?")
    except ConnectionRefusedError as e:
        raise Exception("ConnectionRefusedError creating database pool - did you set the right information in the config, and is the database running?")
    except Exception as e:
        raise Exception("Error creating database pool")
    logger.info("Created database pool successfully")

    # Load the bot's extensions
    logger.info('Loading extensions... ')
    bot.load_all_extensions()

    # Run the bot
    try:
        logger.info("Running bot")
        loop.run_until_complete(bot.start())
    except KeyboardInterrupt:
        logger.info("Logging out bot")
        loop.run_until_complete(bot.logout())

    # We're now done running the bot, time to clean up and close
    logger.info("Closing database pool")
    loop.run_until_complete(utils.DatabaseConnection.pool.close())
    logger.info("Closing asyncio loop")
    loop.close()
