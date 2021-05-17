from aiohttp.web import HTTPFound, Request, Response, RouteTableDef, json_response
from voxelbotutils import web as webutils
import aiohttp_session
import discord
from aiohttp_jinja2 import template

from website import utils as localutils


routes = RouteTableDef()


@routes.get('/login_processor')
async def login_processor(request: Request):
    """
    Page the discord login redirects the user to when successfully logged in with Discord.
    """

    v = await webutils.process_discord_login(request)
    if isinstance(v, Response):
        return HTTPFound('/')
    session = await aiohttp_session.get_session(request)
    return HTTPFound(location=session.pop('redirect_on_login', '/'))


@routes.get('/logout')
async def logout(request: Request):
    """
    Destroy the user's login session.
    """

    session = await aiohttp_session.get_session(request)
    session.invalidate()
    return HTTPFound(location='/')


@routes.get('/login')
async def login(request: Request):
    """
    Direct the user to the bot's Oauth login page.
    """

    return HTTPFound(location=webutils.get_discord_login_url(request, "/login_processor"))


@routes.post('/colour_settings')
async def colour_settings_post_handler(request: Request):
    """
    Handles when people submit their new colours.
    """

    # Grab the colours from their post request
    colours_raw = await request.post()
    try:
        colours_raw = dict(colours_raw)
    except Exception:
        return json_response({"error": "Failed to get dictionary from POST data."}, status=400)

    # Fix up the attributes
    direction = colours_raw.pop("direction")
    colours = {i: -1 if o in ['', 'transparent'] else int(o.strip('#'), 16) for i, o in colours_raw.items()}
    colours['direction'] = direction

    # Save the data to the database
    session = await aiohttp_session.get_session(request)
    user_id = session['user_id']
    async with request.app['database']() as db:
        ctu = await utils.CustomisedTreeUser.get(user_id, db)
        for i, o in colours.items():
            try:
                setattr(ctu, i, o)
            except AttributeError:
                pass
        await ctu.save(db)

    # Redirect back to user settings
    return json_response({"error": None}, status=200)


@routes.post('/set_prefix')
async def set_prefix(request: Request):
    """
    Sets the prefix for a given guild.
    """

    # Make sure the user is allowed to make this request
    checked_data = await localutils.check_user_is_valid(request)
    if isinstance(checked_data, Response):
        return checked_data

    # Grab the prefix they gave
    prefix = checked_data['post_data']['prefix'][:30]
    gold_prefix = checked_data['post_data']['gold_prefix'][:30]

    # Update prefix in DB
    async with request.app['database']() as db:

        await db(
            """INSERT INTO guild_settings (guild_id, prefix, gold_prefix) VALUES ($1, $2, $3)
            ON CONFLICT (guild_id) DO UPDATE SET prefix=excluded.prefix, gold_prefix=excluded.gold_prefix""",
            checked_data['guild_id'], prefix, gold_prefix,
        )
    async with request.app['redis']() as re:
        redis_data = {
            'guild_id': checked_data['guild_id'],
            'prefix': prefix,
            'gold_prefix': gold_prefix,
        }
        await re.publish('UpdateGuildPrefix', redis_data)

    # Redirect to page
    return json_response({"error": ""}, status=200)


@routes.post('/set_gifs_enabled')
async def set_gifs_enabled(request: Request):
    """
    Sets whether or not gifs are enabled for a given guild.
    """

    # Make sure the user is allowed to make this request
    checked_data = await localutils.check_user_is_valid(request)
    if isinstance(checked_data, Response):
        return checked_data

    # Get the maximum members
    try:
        enabled = bool(checked_data['post_data']['enabled'])
    except KeyError:
        enabled = False

    # Get current prefix
    async with request.app['database']() as db:
        await db(
            """INSERT INTO guild_settings (guild_id, gifs_enabled) VALUES ($1, $2)
            ON CONFLICT (guild_id) DO UPDATE SET gifs_enabled=$2""",
            checked_data['guild_id'], enabled,
        )
    async with request.app['redis']() as re:
        await re.publish('UpdateGifsEnabled', {
            'guild_id': checked_data['guild_id'],
            'gifs_enabled': enabled,
        })

    # Redirect to page
    return json_response({"error": ""}, status=200)


@routes.post('/set_incest_enabled')
async def set_incest_enabled(request: Request):
    """
    Sets whether or not incest is enabled for a given guild.
    """

    # Make sure the user is allowed to make this request
    checked_data = await localutils.check_user_is_valid(request)
    if isinstance(checked_data, Response):
        return checked_data

    # Get the maximum members
    try:
        enabled = bool(checked_data['post_data']['enabled'])
    except KeyError:
        enabled = False

    # Get current prefix
    async with request.app['database']() as db:
        await db(
            """INSERT INTO guild_settings (guild_id, allow_incest) VALUES ($1, $2)
            ON CONFLICT (guild_id) DO UPDATE SET allow_incest=$2""",
            checked_data['guild_id'], enabled,
        )
    async with request.app['redis']() as re:
        await re.publish('UpdateIncestAllowed', {
            'guild_id': checked_data['guild_id'],
            'allow_incest': enabled,
        })

    # Redirect to page
    return json_response({"error": ""}, status=200)


@routes.post('/set_max_allowed_children')
async def set_max_allowed_children(request: Request):
    """
    Sets the maximum allowed children for each given role.
    """

    # Make sure the user is allowed to make this request
    checked_data = await localutils.check_user_is_valid(request)
    if isinstance(checked_data, Response):
        return checked_data

    # Get current prefix
    data = checked_data["post_data"].copy()
    guild_id = int(data.pop("guild_id"))
    max_children_dict = {}
    async with request.app['database']() as db:
        await db.start_transaction()
        await db("""DELETE FROM max_children_amount WHERE guild_id=$1""", guild_id)
        for role_id, amount in data.items():
            try:
                await db(
                    """INSERT INTO max_children_amount (guild_id, role_id, amount) VALUES ($1, $2, $3)
                    ON CONFLICT DO NOTHING""",
                    guild_id, int(role_id), int(amount),
                )
                max_children_dict[int(role_id)] = int(amount)
            except ValueError:
                pass
        await db.commit_transaction()
    async with request.app['redis']() as re:
        await re.publish('UpdateMaxChildren', {
            'guild_id': checked_data['guild_id'],
            'max_children': max_children_dict,
        })

    # Redirect to page
    return json_response({"error": ""}, status=200)


@routes.post('/unblock_user')
async def unblock_user_post_handler(request: Request):
    """
    Handles when people submit their new colours.
    """

    # Make sure the user is allowed to make this request
    if not webutils.is_logged_in(request):
        return json_response({"error": "You need to be logged in to use this endpoint."}, status=401)

    # Get the POST data
    try:
        post_data = await request.json()
    except Exception:
        return json_response({"error": "Invalid JSON provided."}, status=400)

    # Get blocked user
    try:
        blocked_user = int(post_data['user_id'])
    except ValueError:
        return json_response({"error": "Invalid blocked user ID provided."}, status=400)

    # Get logged in user
    session = await aiohttp_session.get_session(request)
    logged_in_user = session['user_id']

    # Remove data
    async with request.app['database']() as db:
        await db(
            """DELETE FROM blocked_user WHERE user_id=$1 AND blocked_user_id=$2""",
            logged_in_user, blocked_user,
        )
    async with request.app['redis']() as re:
        await re.publish("BlockedUserRemove", {"user_id": logged_in_user, "blocked_user_id": blocked_user})

    # Redirect back to user settings
    return json_response({"error": ""}, status=200)


@routes.post('/colour_settings')
async def colour_settings_post_handler(request:Request):
    """
    Handles when people submit their new colours.
    """

    # Make sure the user is allowed to make this request
    if not webutils.is_logged_in(request):
        return json_response({"error": "You need to be logged in to use this endpoint."}, status=401)

    # Get the POST data
    try:
        post_data = await request.json()
    except Exception:
        return json_response({"error": "Invalid JSON provided."}, status=400)

    # Get logged in user
    session = await aiohttp_session.get_session(request)
    logged_in_user = session['user_id']

    # Fix up the attributes
    direction = post_data.pop("direction")
    colours = {i: -1 if o in ['', 'transparent'] else int(o.strip('#'), 16) for i, o in post_data.items()}
    colours['direction'] = direction

    # Save the data to the database
    async with request.app['database']() as db:
        ctu = await utils.CustomisedTreeUser.get(logged_in_user, db)
        for i, o in colours.items():
            setattr(ctu, i, o)
        await ctu.save(db)

    # Redirect back to user settings
    return json_response({"error": ""}, status=200)
