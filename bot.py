from argparse import ArgumentParser
from warnings import filterwarnings
import logging
import os

import discord

from cogs import utils


# Set up loggers
logging.basicConfig(format='%(name)s:%(levelname)s: %(message)s')
logger = logging.getLogger(os.getcwd().split(os.sep)[-1].split()[-1].lower())

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

# Make sure the sharding info provided is correctish
if args.shardcount is None:
    shard_ids = None
else:
    shard_ids = list(range(args.min, args.max+1))
if args.shardcount is None and (args.min or args.max):
    logger.critical("You set a min/max shard handler but no shard count")
    exit(1)
if args.shardcount is not None and not (args.min is not None and args.max is not None):
    logger.critical("You set a shardcount but not min/max shards")
    exit(1)

# Okay cool make the bot object
bot = utils.CustomBot(
    config_file=args.config_file,
    activity=discord.Game(name="Reconnecting..."),
    status=discord.Status.dnd,
    case_insensitive=True,
    shard_count=args.shardcount,
    shard_ids=shard_ids,
    shard_id=args.min,
    max_messages=100,  # The lowest amount that we can actually cache
    logger=logger.getChild('bot')
)

# Set up our loggers
log_level = getattr(logging, args.loglevel.upper(), None)
if log_level is None:
    raise Exception("Invalid log level provided")
logger.setLevel(log_level)
logging.getLogger("discord").setLevel(logging.INFO)


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

    # Connect the database
    logger.info("Creating database pool")
    try:
        db_connect = utils.DatabaseConnection.create_pool(bot.config['database'])
        loop.run_until_complete(db_connect)
    except KeyError as e:
        logger.critical("KeyError creating database pool - "
                        "is there a 'database' object in the config?")
        raise e
    except ConnectionRefusedError as e:
        logger.critical("ConnectionRefusedError creating database pool - "
                        "did you set the right information in the config, "
                        "and is the database running?")
        raise e
    except Exception as e:
        logger.critical("Error creating database pool")
        raise e
    logger.info("Created database pool successfully")

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
