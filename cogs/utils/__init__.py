from cogs.utils import checks, converters, errors, random_text
from cogs.utils.proposal_message_checker import proposal_message_checker, TickPayloadCheckResult
from cogs.utils.customised_tree_user import CustomisedTreeUser
from cogs.utils.family_tree.family_tree_member import FamilyTreeMember
from cogs.utils.family_tree.relationship_string_simplifier import RelationshipStringSimplifier
from cogs.utils.proposal_cache import ProposalCache


def get_family_guild_id(ctx) -> int:
    if ctx.bot.config['is_server_specific']:
        return ctx.guild.id
    return 0
