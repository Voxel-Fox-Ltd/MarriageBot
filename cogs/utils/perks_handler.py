import voxelbotutils


class MarriageBotPerks(object):

    __slots__ = (
        "max_children", "max_partners", "can_run_stupidtree",
        "can_run_disownall", "tree_command_cooldown",
    )

    def __init__(
            self, max_children:int=5, max_partners:int=1, can_run_stupidtree:bool=False,
            can_run_disownall:bool=False, tree_command_cooldown:int=60):
        self.max_children = max_children
        self.max_partners = max_partners
        self.can_run_stupidtree = can_run_stupidtree
        self.can_run_disownall = can_run_disownall
        self.tree_command_cooldown = tree_command_cooldown


async def get_marriagebot_perks(bot:voxelbotutils.Bot, ctx:voxelbotutils.Context) -> MarriageBotPerks:
    """
    Get the specific perks that any given user has.

    Args:
        bot (voxelbotutils.Bot): The bot instance that will be used to fetch data from Upgrade.Chat.
        ctx (voxelbotutils.Context): The context object for the command that is being called.

    Returns:
        MarriageBotPerks: All of the perks that the calling user has.
    """

    # Override stuff for owners
    if ctx.author.id in bot.owner_ids:
        return MarriageBotPerks(
            max_children=30,
            can_run_stupidtree=True,
            can_run_disownall=True,
            tree_command_cooldown=5,
        )

    # Check UpgradeChat purchases
    purchases = await bot.upgrade_chat.get_orders(discord_id=ctx.author.id)
    purchased_item_names = []
    [purchased_item_names.extend(i.order_item_names) for i in purchases]
    if "MarriageBot Subscription Tier 3" in purchased_item_names:
        return MarriageBotPerks(
            max_children=20,
            can_run_stupidtree=True,
            can_run_disownall=True,
            tree_command_cooldown=5,
        )
    elif "MarriageBot Subscription Tier 2" in purchased_item_names:
        return MarriageBotPerks(
            max_children=15,
            can_run_stupidtree=True,
            can_run_disownall=True,
            tree_command_cooldown=15,
        )
    elif "MarriageBot Subscription Tier 1" in purchased_item_names:
        return MarriageBotPerks(
            max_children=10,
            can_run_disownall=True,
            tree_command_cooldown=15,
        )

    # Check Top.gg votes
    try:
        await voxelbotutils.checks.is_voter().predicate(ctx)
        return MarriageBotPerks(
            tree_command_cooldown=30,
        )
    except Exception:
        pass

    # Return default
    return MarriageBotPerks()
