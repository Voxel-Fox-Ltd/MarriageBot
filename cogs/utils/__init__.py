from typing import TYPE_CHECKING

from cogs.utils import (
    checks,
    converters,
    errors,
    types,
)
from cogs.utils.proposal_message_checker import (
    send_proposal_message,
    TickPayloadCheckResult,
    ProposalLock,
    ProposalInProgress,
    only_mention,
    escape_markdown,
)
from cogs.utils.customised_tree_user import CustomisedTreeUser
from cogs.utils.family_tree.family_tree_member import FamilyTreeMember
from cogs.utils.family_tree.relationship_string_simplifier import RelationshipStringSimplifier
from cogs.utils.discord_name_manager import DiscordNameManager
from cogs.utils.perks_handler import (
    get_marriagebot_perks,
    TIER_NONE,
    TIER_ONE,
    TIER_TWO,
    TIER_THREE,
    TIER_VOTER,
    MarriageBotPerks,
)

if TYPE_CHECKING:
    from discord.ext import vbu


__all__ = (
    'checks',
    'converters',
    'errors',
    'types',
    'send_proposal_message',
    'TickPayloadCheckResult',
    'ProposalLock',
    'ProposalInProgress',
    'only_mention',
    'escape_markdown',
    'CustomisedTreeUser',
    'FamilyTreeMember',
    'RelationshipStringSimplifier',
    'DiscordNameManager',
    'get_marriagebot_perks',
    'TIER_NONE',
    'TIER_ONE',
    'TIER_TWO',
    'TIER_THREE',
    'TIER_VOTER',
    'MarriageBotPerks',
    'get_family_guild_id',
    'guild_allows_incest',
    'get_max_family_members',
)


def get_family_guild_id(ctx: vbu.Context) -> int:
    """
    Get the guild ID associated with a context object to save
    for a family.
    """

    if ctx.bot.config['is_server_specific']:
        if ctx.guild is None:
            return 0
        return ctx.guild.id
    return 0


def guild_allows_incest(ctx: vbu.Context) -> bool:
    """
    See if a given guild allows incest.
    """

    if get_family_guild_id(ctx) == 0:
        return False
    return ctx.bot.guild_settings[ctx.guild.id]['allow_incest']


def get_max_family_members(ctx: vbu.Context) -> int:
    """
    Get the maximum set family members for a given guild.
    Basically just a switch case for whether the bot is server
    specific or not.
    """

    if get_family_guild_id(ctx) == 0:
        return ctx.bot.config['max_family_members']
    return ctx.bot.guild_settings[ctx.guild.id]['max_family_members']
