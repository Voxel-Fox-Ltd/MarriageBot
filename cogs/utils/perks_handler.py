import asyncio
import collections
from datetime import datetime as dt, timedelta
import functools
from typing import Awaitable, Callable, Dict, Optional, Tuple

from discord.ext import vbu


__all__ = (
    'MarriageBotPerks',
    'get_marriagebot_perks',
    'TIER_THREE',
    'TIER_TWO',
    'TIER_ONE',
    'TIER_VOTER',
    'TIER_NONE',
)


class MarriageBotPerks(object):

    __slots__ = (
        "max_children",
        "max_partners",
        "can_run_fulltree",
        "can_run_disownall",
        "tree_command_cooldown",
        "tree_render_quality",
        "can_run_abandon",
    )

    def __init__(
            self,
            max_children: int = 5,
            max_partners: int = 1,
            can_run_fulltree: bool = False,
            can_run_disownall: bool = False,
            tree_command_cooldown: int = 60,
            tree_render_quality: int = 0,
            can_run_abandon: bool = False):
        self.max_children = max_children
        self.max_partners = max_partners
        self.can_run_fulltree = can_run_fulltree
        self.can_run_disownall = can_run_disownall
        self.tree_command_cooldown = tree_command_cooldown
        self.tree_render_quality = tree_render_quality
        self.can_run_abandon = can_run_abandon


# £7
TIER_THREE = MarriageBotPerks(
    max_children=20,
    can_run_fulltree=True,
    can_run_disownall=True,
    can_run_abandon=True,
    tree_command_cooldown=5,
    tree_render_quality=3,
    max_partners=8,
)

# £5
TIER_TWO = MarriageBotPerks(
    max_children=15,
    can_run_fulltree=True,
    can_run_disownall=True,
    can_run_abandon=True,
    tree_command_cooldown=15,
    tree_render_quality=2,
    max_partners=4,
)

# £3
TIER_ONE = MarriageBotPerks(
    max_children=10,
    can_run_disownall=True,
    tree_command_cooldown=15,
    tree_render_quality=1,
    max_partners=2,
)

# Vote
TIER_VOTER = MarriageBotPerks(
    tree_command_cooldown=30,
)

# Default
TIER_NONE = MarriageBotPerks()


tier_mapping = {
    3: TIER_THREE,
    2: TIER_TWO,
    1: TIER_ONE,
    0: TIER_NONE,
}


_CACHED_PERK_ITEMS: Dict[int, Tuple[Optional[MarriageBotPerks], dt]]
_CACHED_PERK_ITEMS = collections.defaultdict(lambda: (None, dt(2000, 1, 1),))


def perks_cache(func: Callable[[vbu.Bot, int], Awaitable[MarriageBotPerks]]):
    lifetime = {"minutes": 2}

    @functools.wraps(func)
    async def wrapper(bot: vbu.Bot, user_id: int) -> MarriageBotPerks:
        perks, expiry_time = _CACHED_PERK_ITEMS[user_id]
        if expiry_time > dt.utcnow() and perks:
            return perks  # Cache not expired
        perks = await func(bot, user_id)
        _CACHED_PERK_ITEMS[user_id] = (
            perks,
            dt.utcnow() + timedelta(**lifetime),
        )
        return perks
    return wrapper


@perks_cache
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
        rows = await db(
            """
            SELECT
                *
            FROM
                guild_specific_families
            WHERE
                purchased_by = $1
            """,
            user_id,
        )
    if rows:
        return TIER_THREE

    # Check VFL purchases
    url = "https://voxelfox.co.uk/api/portal/check"
    params = {
        "product_id": "b6586947-0ce4-4b1c-bf27-6713b33409d3",
        "discord_user_id": user_id,
    }
    try:
        async with bot.session.get(url, params=params, timeout=3) as r:
            data = await r.json()
    except Exception:
        data = {}
    if data.get("success", False) and data.get("result"):
        purchase_item_ids = [
            i["product_id"]
            for i in data["purchases"]
        ]
        purchased_products = [
            data["products"][i]["product_name"]
            for i in purchase_item_ids
        ]
        tier = max([
            int(i.split(" ")[-1])
            for i in purchased_products
        ])
        return tier_mapping[tier]

    # Check Top.gg votes
    try:
        aw = bot.get_user_topgg_vote(user_id)
        data = await asyncio.wait_for(aw, timeout=3)
        if data:
            return TIER_VOTER
    except asyncio.TimeoutError:
        pass
    return tier_mapping[0]
