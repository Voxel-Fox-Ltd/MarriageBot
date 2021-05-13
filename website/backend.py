from aiohttp.web import HTTPFound, Request, Response, RouteTableDef
from voxelbotutils import web as webutils
import aiohttp_session
import discord
from aiohttp_jinja2 import template


routes = RouteTableDef()


@routes.get('/login_processor')
async def login_processor(request:Request):
    """
    Page the discord login redirects the user to when successfully logged in with Discord.
    """

    v = await webutils.process_discord_login(request)
    if isinstance(v, Response):
        return HTTPFound('/')
    session = await aiohttp_session.get_session(request)
    return HTTPFound(location=session.pop('redirect_on_login', '/'))


@routes.get('/logout')
async def logout(request:Request):
    """
    Destroy the user's login session.
    """

    session = await aiohttp_session.get_session(request)
    session.invalidate()
    return HTTPFound(location='/')


@routes.get('/login')
async def login(request:Request):
    """
    Direct the user to the bot's Oauth login page.
    """

    return HTTPFound(location=webutils.get_discord_login_url(request, "/login_processor"))


@routes.post('/colour_settings')
@webutils.requires_login()
async def colour_settings_post_handler(request: Request):
    """
    Handles when people submit their new colours.
    """

    # Grab the colours from their post request
    colours_raw = await request.post()
    try:
        colours_raw = dict(colours_raw)
    except Exception:
        return Response(status=400)

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
            setattr(ctu, i, o)
        await ctu.save(db)

    # Redirect back to user settings
    return Response(status=200)


@routes.post('/unblock_user')
@webutils.requires_login()
async def unblock_user_post_handler(request: Request):
    """
    Handles when people submit their new colours.
    """

    # Get data
    post_data_raw = await request.post()

    # Get blocked user
    try:
        blocked_user = int(post_data_raw['user_id'])
    except ValueError:
        return HTTPFound(location='/user_settings')

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
    return HTTPFound(location='/user_settings')


@routes.post('/set_prefix')
@webutils.requires_login()
async def set_prefix(request:Request):
    """
    Sets the prefix for a given guild.
    """

    # See if they're logged in
    session = await aiohttp_session.get_session(request)
    if not session.get('user_id'):
        return HTTPFound(location='/')

    # Get the guild we're looking at
    post_data = await request.post()
    guild_id = post_data['guild_id']
    if not guild_id:
        return HTTPFound(location='/')

    # See if they're allowed to change this guild
    all_guilds = await webutils.get_user_guilds(request)
    if all_guilds is None:
        return HTTPFound(location='/discord_oauth_login')
    guild = [i for i in all_guilds if (i['owner'] or i['permissions'] & 40 > 0) and guild_id == i['id']]
    if not guild:
        return HTTPFound(location='/')

    # Grab the prefix they gave
    prefix = post_data['prefix'][0:30]
    if len(prefix) == 0:
        if post_data.get('gold', False):
            prefix = request.app['gold_config']['prefix']['default_prefix']
        else:
            prefix = request.app['config']['prefix']['default_prefix']

    # Update prefix in DB
    async with request.app['database']() as db:
        if post_data['gold']:
            key = 'gold_prefix'
        else:
            key = 'prefix'
        await db(f'INSERT INTO guild_settings (guild_id, {key}) VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET {key}=$2', int(guild_id), prefix)
    async with request.app['redis']() as re:
        redis_data = {'guild_id': int(guild_id)}
        redis_data[{True: 'gold_prefix', False: 'prefix'}[bool(post_data['gold'])]] = prefix
        await re.publish('UpdateGuildPrefix', redis_data)

    # Redirect to page
    location = f'/guild_settings?guild_id={guild_id}&gold=1' if post_data['gold'] else f'/guild_settings?guild_id={guild_id}'
    return HTTPFound(location=location)
