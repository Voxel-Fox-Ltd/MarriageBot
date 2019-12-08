import hmac
import hashlib

import aiohttp
from aiohttp.web import RouteTableDef, Request, HTTPFound, Response
import aiohttp_session
import json
import asyncpg

from cogs import utils
from website import utils as webutils


"""
All pages on this website that implement the base.jinja file should return two things:
Firstly, the original request itself under the name 'request'.
Secondly, it should return the user info from the user as gotten from the login under 'user_info'
This is all handled by a decorator below, but I'm just putting it here as a note
"""


routes = RouteTableDef()
OAUTH_SCOPES = 'identify guilds'
DISCORD_OAUTH_URL = 'https://discordapp.com/api/oauth2/authorize?'


@routes.get("/r/{code}")
async def redirect(request:Request):
    """Handles redirects using codes stored in the db"""

    code = request.match_info['code']
    async with request.app['database']() as db:
        data = await db("SELECT location FROM redirects WHERE code=$1", code)
    if not data:
        return HTTPFound(location='/')
    return HTTPFound(location=data[0]['location'])


@routes.get('/login')
async def login(request:Request):
    """Page the discord login redirects the user to when successfully logged in with Discord"""

    # Get the code
    code = request.query.get('code')
    if not code:
        return HTTPFound(location='/')

    # Get the bot
    config = request.app['config']
    oauth_data = config['oauth']

    # Generate the post data
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'scope': OAUTH_SCOPES
    }
    data.update(oauth_data)
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    # Make the request
    async with aiohttp.ClientSession(loop=request.loop) as session:

        # Get auth
        token_url = f"https://discordapp.com/api/v6/oauth2/token"
        async with session.post(token_url, data=data, headers=headers) as r:
            token_info = await r.json()

        # Get user
        headers.update({
            "Authorization": f"{token_info['token_type']} {token_info['access_token']}"
        })
        user_url = f"https://discordapp.com/api/v6/users/@me"
        async with session.get(user_url, headers=headers) as r:
            user_info = await r.json()

        # Get guilds
        guilds_url = f"https://discordapp.com/api/v6/users/@me/guilds"
        async with session.get(guilds_url, headers=headers) as r:
            guild_info = await r.json()

    # Save to session
    session = await aiohttp_session.new_session(request)
    user_info['avatar_link'] = webutils.get_avatar(user_info)
    session['user_info'] = user_info
    session['guild_info'] = guild_info
    session['user_id'] = int(user_info['id'])

    # Redirect to settings
    return HTTPFound(location=f'/settings')


@routes.post('/colour_settings')
async def colour_settings_post_handler(request:Request):
    """Handles when people submit their new colours"""

    try:
        colours_raw = await request.post()
    except Exception as e:
        raise e
    colours_raw = dict(colours_raw)
    direction = colours_raw.pop("direction")
    colours = {i: -1 if o in ['', 'transparent'] else int(o.strip('#'), 16) for i, o in colours_raw.items()}
    colours['direction'] = direction
    session = await aiohttp_session.get_session(request)
    user_id = session['user_id']
    async with request.app['database']() as db:
        ctu = await utils.CustomisedTreeUser.get(user_id, db)
    for i, o in colours.items():
        setattr(ctu, i, o)
    async with request.app['database']() as db:
        await ctu.save(db)
    return HTTPFound(location='/user_settings')


@routes.post('/unblock_user')
async def unblock_user_post_handler(request:Request):
    """Handles when people submit their new colours"""

    # Get data
    try:
        post_data_raw = await request.post()
    except Exception as e:
        raise e

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
            "DELETE FROM blocked_user WHERE user_id=$1 AND blocked_user_id=$2",
            logged_in_user, blocked_user
        )
    async with request.app['redis']() as re:
        await re.publish_json("BlockedUserRemove", {"user_id": logged_in_user, "blocked_user_id": blocked_user})
    return HTTPFound(location='/user_settings')


@routes.post('/guild_settings')
async def guild_settings_post(request:Request):
    """Shows the settings for a particular guild"""

    # See if they're logged in
    session = await aiohttp_session.get_session(request)
    if not session.get('user_id'):
        return HTTPFound(location='/')
    guild_id = request.query.get('guild_id')
    if not guild_id:
        return HTTPFound(location='/')

    # Get the guilds they're valid to alter
    all_guilds = session['guild_info']
    guild = [i for i in all_guilds if (i['owner'] or i['permissions'] & 40 > 0) and guild_id == i['id']]
    if not guild:
        return HTTPFound(location='/')
    data = await request.post()
    prefix = data['prefix'][0:30]

    # Get current prefix
    async with request.app['database']() as db:
        await db('UPDATE guild_settings SET prefix=$1 WHERE guild_id=$2', prefix, int(guild_id))
    async with request.app['redis']() as re:
        await re.publish_json('UpdateGuildPrefix', {
            'guild_id': int(guild_id),
            'prefix': prefix,
        })
    return HTTPFound(location=f'/guild_settings?guild_id={guild_id}')


@routes.post('/guild_gold_settings')
async def guild_gold_settings_post(request:Request):
    """Shows the settings for a particular guild"""

    # See if they're logged in
    session = await aiohttp_session.get_session(request)
    if not session.get('user_id'):
        return HTTPFound(location='/')
    guild_id = request.query.get('guild_id')
    if not guild_id:
        return HTTPFound(location='/')

    # Get the guilds they're valid to alter
    all_guilds = session['guild_info']
    guild = [i for i in all_guilds if (i['owner'] or i['permissions'] & 40 > 0) and guild_id == i['id']]
    if not guild:
        return HTTPFound(location='/')
    data = await request.post()
    prefix = data['prefix'][0:30]

    # Get current prefix
    async with request.app['database']() as db:
        await db('UPDATE guild_settings SET gold_prefix=$1 WHERE guild_id=$2', prefix, int(guild_id))
    async with request.app['redis']() as re:
        await re.publish_json('UpdateGuildPrefix', {
            'guild_id': int(guild_id),
            'gold_prefix': prefix,
        })
    return HTTPFound(location=f'/guild_gold_settings?guild_id={guild_id}')


@routes.post('/webhooks/stripe/purchase_complete')
async def purchase_complete(request:Request):
    """Handles Stripe throwing data my way"""

    # Decode the data
    content_bytes: bytes = await request.content.read()
    stripe_data: dict = json.loads(content_bytes.decode())

    # Check the signature of the payload
    signature: str = request.headers['Stripe-Signature']
    signature_params = {i.strip().split('=')[0]: i.strip().split('=')[1] for i in signature.split(',')}
    computed_signature = hmac.new(
        request.app['config']['stripe']['signing_key'].encode(),
        f"{signature_params['t']}.{content_bytes.decode()}".encode(),
        digestmod=hashlib.sha256
    ).hexdigest()
    if signature_params['v1'] != computed_signature:
        return Response(status=200)  # invalid signature

    # Grab data from db
    db = await request.app['database'].get_connection()
    database_data = await db("SELECT * FROM stripe_purchases WHERE id=$1", stripe_data['data']['object']['id'])
    if database_data is None:
        return Response(status=200)  # no transaction ID in DB

    # Update db with data
    await db(
        "UPDATE stripe_purchases SET customer_id=$1, completed=true, checkout_complete_timestamp=NOW() WHERE id=$2",
        stripe_data['data']['object']['customer'], stripe_data['data']['object']['id']
    )
    try:
        await db("INSERT INTO guild_specific_families VALUES ($1)", database_data[0]['guild_id'])
    except asyncpg.UniqueViolationError:
        pass
    await db.disconnect()

    # Let the user get redirected
    return Response(status=200)
