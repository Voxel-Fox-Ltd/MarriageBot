import aiohttp_session
from aiohttp.web import Request, json_response
from voxelbotutils import web as webutils

from website import utils as localutils


async def check_user_is_valid(request: Request):
    """
    Checks if a request is valid, returning a Response object if it isn't, and a
    dictionary of data things if it is.
    """

    # See if they're logged in
    if not webutils.is_logged_in(request):
        return json_response({"error": "User isn't logged in."}, status=401)

    # Get the POST data
    try:
        post_data = await request.json()
    except Exception:
        return json_response({"error": "Invalid JSON provided."}, status=400)

    # Get the guild we're looking at
    guild_id = post_data.get('guild_id')
    if not guild_id:
        return json_response({"error": "No guild ID provided."}, status=400)
    try:
        guild_id = int(guild_id)
    except ValueError:
        return json_response({"error": "Invalid guild ID provided."}, status=400)

    # Get the guild member
    guild = await localutils.get_guild(request, guild_id)
    if not guild:
        return json_response({"error": "Invalid guild ID provided."}, status=400)
    session = await aiohttp_session.get_session(request)
    user_id = session.get("user_id")
    try:
        member = await guild.fetch_member(user_id)
    except discord.HTTPException:
        return json_response({"error": "User not found in guild."}, status=401)

    # See if they're allowed to change this guild
    if guild.owner_id == member.id or member.guild_permissions.manage_guild:
        pass
    else:
        return json_response({"error": "User does not have permission to manage this guild."}, status=401)

    # Sick everything's done
    return {
        'post_data': post_data,
        'guild_id': guild_id,
        'guild': guild,
        'session': session,
        'user_id': user_id,
        'member': member,
    }
