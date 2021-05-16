import typing

import discord
from aiohttp.web import Request


async def get_guild(request: Request, guild_id: int) -> typing.Optional[discord.Guild]:
    """
    Tries to fetch the guild object from the two bot objects that are stored
    in the request.
    """

    try:
        guild_object = await request.app['bots']['bot'].fetch_guild(guild_id)
    except discord.Forbidden:
        try:
            guild_object = await request.app['bots']['gold_bot'].fetch_guild(guild_id)
        except discord.Forbidden:
            return None
    return guild_object
