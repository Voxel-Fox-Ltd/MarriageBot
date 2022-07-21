from typing import List, TypedDict, Dict

from discord.ext import vbu


__all__ = (
    'FamilyTreeMemberPayload',
    'GuildPrefixPayload',
    'FamilyMaxMembersPayload',
    'IncestAllowedPayload',
    'MaxChildrenPayload',
    'GifsEnabledPayload',
    'SendUserMessagePayload',
    'GuildConfig',
    'MarriageBotConfig',
    'Bot',
)


class FamilyTreeMemberPayload(TypedDict):
    discord_id: int
    children: List[int]
    parent_id: int
    partner_id: int
    guild_id: int


class GuildPrefixPayload(TypedDict):
    guild_id: int
    prefix: str


class FamilyMaxMembersPayload(TypedDict):
    guild_id: int
    max_family_members: int


class IncestAllowedPayload(TypedDict):
    guild_id: int
    allow_incest: bool


class MaxChildrenPayload(TypedDict):
    guild_id: int
    max_children: Dict[int, int]


class GifsEnabledPayload(TypedDict):
    guild_id: int
    gifs_enabled: bool


class SendUserMessagePayload(TypedDict):
    user_id: int
    content: str


class GuildConfig(TypedDict):
    guild_id: int
    prefix: str
    gold_prefix: str
    test_prefix: str
    allow_incest: bool
    max_family_members: int
    gifs_enabled: bool
    max_children: Dict[int, int]


class APIKeysConfig(TypedDict):
    weebsh: str


class MarriageBotConfig(vbu.types.BotConfig):
    max_family_members: int
    tree_file_location: str
    is_server_specific: bool
    api_keys: APIKeysConfig


class Bot(vbu.Bot):
    config: MarriageBotConfig
    guild_settings: Dict[int, GuildConfig]
