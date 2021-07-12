import asyncio
import collections
from datetime import datetime as dt, timedelta

import voxelbotutils as vbu


class MarriageBotPerks(object):

    __slots__ = (
        "max_children", "max_partners", "can_run_bloodtree",
        "can_run_disownall", "tree_command_cooldown", "tree_render_quality",
        "can_run_abandon",
    )

    def __init__(
            self, max_children: int = 5, max_partners: int = 1, can_run_bloodtree: bool = False,
            can_run_disownall: bool = False, tree_command_cooldown: int = 60, tree_render_quality: int = 0,
            can_run_abandon: bool = False):
        self.max_children = max_children
        self.max_partners = max_partners
        self.can_run_bloodtree = can_run_bloodtree
        self.can_run_disownall = can_run_disownall
        self.tree_command_cooldown = tree_command_cooldown
        self.tree_render_quality = tree_render_quality
        self.can_run_abandon = can_run_abandon


TIER_THREE = MarriageBotPerks(
    max_children=20,
    can_run_bloodtree=True,
    can_run_disownall=True,
    can_run_abandon=True,
    tree_command_cooldown=5,
    tree_render_quality=3
)
TIER_TWO = MarriageBotPerks(
    max_children=15,
    can_run_bloodtree=True,
    can_run_disownall=True,
    can_run_abandon=True,
    tree_command_cooldown=15,
    tree_render_quality=2
)
TIER_ONE = MarriageBotPerks(
    max_children=10,
    can_run_disownall=True,
    tree_command_cooldown=15,
    tree_render_quality=1
)
TIER_VOTER = MarriageBotPerks(
    tree_command_cooldown=30,
)
TIER_NONE = MarriageBotPerks()


CACHED_PERK_ITEMS = collections.defaultdict(lambda: (None, dt(2000, 1, 1),))


def cache_response(**lifetime):
    def inner(func):
        async def wrapper(bot: vbu.Bot, user_id: int):
            perks, expiry_time = CACHED_PERK_ITEMS[user_id]
            if expiry_time > dt.utcnow():
                return perks  # Cache not expired
            perks = await func(bot, user_id)
            CACHED_PERK_ITEMS[user_id] = (perks, dt.utcnow() + timedelta(**lifetime),)
            return perks
        return wrapper
    return inner


@cache_response(minutes=2)
async def get_marriagebot_perks(bot: vbu.Bot, user_id: int) -> MarriageBotPerks:
    """
    Get the specific perks that any given user has.

    Args:
        bot (utils.Bot): The bot instance that will be used to fetch data from Upgrade.Chat.
        user_id (int): The ID of the user we want to get the perks of.

    Returns:
        MarriageBotPerks: All of the perks that the calling user has.
    """

    # Override stuff for owners
    if user_id in bot.owner_ids:
        return TIER_THREE

    # Check if they have a purchase
    async with bot.database() as db:
        rows = await db("SELECT * FROM guild_specific_families WHERE purchased_by=$1", user_id)
    if rows:
        return TIER_THREE

    # Check UpgradeChat purchases
    try:
        purchases = await asyncio.wait_for(bot.upgrade_chat.get_orders(discord_id=user_id), timeout=3)
    except asyncio.TimeoutError:
        purchases = []
    purchased_item_names = []
    [purchased_item_names.extend(i.order_item_names) for i in purchases]
    if "MarriageBot Subscription Tier 3" in purchased_item_names:
        return TIER_THREE
    elif "MarriageBot Subscription Tier 2" in purchased_item_names:
        return TIER_TWO
    elif "MarriageBot Subscription Tier 1" in purchased_item_names:
        return TIER_ONE

    # Check Top.gg votes
    try:
        data = await asyncio.wait_for(bot.get_user_topgg_vote(user_id), timeout=3)
        if data:
            return TIER_VOTER
    except asyncio.TimeoutError:
        pass

    # Return default
    return MarriageBotPerks()
