import json
from datetime import datetime as dt

import aiohttp_session
from aiohttp.web import HTTPFound, Request, Response, RouteTableDef

from cogs import utils
from website import utils as webutils


routes = RouteTableDef()


@routes.get("/r/{code}")
async def redirect(request:Request):
    """Handles redirects using codes stored in the db"""

    code = request.match_info['code']
    async with request.app['database']() as db:
        data = await db("SELECT location FROM redirects WHERE code=$1", code)
    if not data:
        return HTTPFound(location='/')
    return HTTPFound(location=data[0]['location'])


@routes.post('/colour_settings')
@webutils.requires_login()
async def colour_settings_post_handler(request:Request):
    """Handles when people submit their new colours"""

    # Grab the colours from their post request
    try:
        colours_raw = await request.post()
    except Exception as e:
        raise e
    colours_raw = dict(colours_raw)

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
    return HTTPFound(location='/user_settings')


@routes.post('/unblock_user')
@webutils.requires_login()
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

    # Redirect back to user settings
    return HTTPFound(location='/user_settings')


@routes.post('/set_prefix')
@webutils.requires_login()
async def set_prefix(request:Request):
    """Sets the prefix for a given guild"""

    # See if they're logged in
    session = await aiohttp_session.get_session(request)
    post_data = await request.post()
    if not session.get('user_id'):
        return HTTPFound(location='/')
    guild_id = post_data['guild_id']
    if not guild_id:
        return HTTPFound(location='/')

    # Get the guilds they're valid to alter
    all_guilds = await webutils.get_user_guilds(request)
    if all_guilds is None:
        return HTTPFound(location='/discord_oauth_login')
    guild = [i for i in all_guilds if (i['owner'] or i['permissions'] & 40 > 0) and guild_id == i['id']]
    if not guild:
        return HTTPFound(location='/')

    # Grab the prefix they gave
    prefix = post_data['prefix'][0:30]
    if len(prefix) == 0:
        if post_data['gold']:
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
        await re.publish_json('UpdateGuildPrefix', redis_data)

    # Redirect to page
    location = f'/guild_settings?guild_id={guild_id}&gold=1' if post_data['gold'] else f'/guild_settings?guild_id={guild_id}'
    return HTTPFound(location=location)


@routes.post('/set_max_family_members')
@webutils.requires_login()
async def set_max_family_members(request:Request):
    """Sets the maximum family members for a given guild"""

    # See if they're logged in
    post_data = await request.post()
    guild_id = post_data['guild_id']
    if not guild_id:
        return HTTPFound(location='/')

    # Get the guilds they're valid to alter
    all_guilds = await webutils.get_user_guilds(request)
    if all_guilds is None:
        return HTTPFound(location='/discord_oauth_login')
    guild = [i for i in all_guilds if (i['owner'] or i['permissions'] & 40 > 0) and guild_id == i['id']]
    if not guild:
        return HTTPFound(location='/')

    # Get the maximum members
    try:
        max_members = int(post_data['amount'])
        assert max_members >= 50
    except ValueError:
        max_members = request.app['config']['max_family_members']
    except AssertionError:
        max_members = 50
    max_members = min([max_members, 2000])

    # Get current prefix
    async with request.app['database']() as db:
        await db('INSERT INTO guild_settings (guild_id, max_family_members) VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET max_family_members=$2', int(guild_id), max_members)
    async with request.app['redis']() as re:
        await re.publish_json('UpdateFamilyMaxMembers', {
            'guild_id': int(guild_id),
            'max_family_members': max_members,
        })

    # Redirect to page
    return HTTPFound(location=f'/guild_settings?guild_id={guild_id}&gold=1')


@routes.post('/set_gifs_enabled')
@webutils.requires_login()
async def set_gifs_enabled(request:Request):
    """Sets whether or not gifs are enabled for a given guild"""

    # See if they're logged in
    post_data = await request.post()
    guild_id = post_data['guild_id']
    if not guild_id:
        return HTTPFound(location='/')

    # Get the guilds they're valid to alter
    all_guilds = await webutils.get_user_guilds(request)
    if all_guilds is None:
        return HTTPFound(location='/discord_oauth_login')
    guild = [i for i in all_guilds if (i['owner'] or i['permissions'] & 40 > 0) and guild_id == i['id']]
    if not guild:
        return HTTPFound(location='/')

    # Get the maximum members
    try:
        enabled = bool(post_data['enabled'])
    except KeyError:
        enabled = False

    # Get current prefix
    async with request.app['database']() as db:
        await db('INSERT INTO guild_settings (guild_id, gifs_enabled) VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET gifs_enabled=$2', int(guild_id), enabled is True)
    async with request.app['redis']() as re:
        await re.publish_json('UpdateGifsEnabled', {
            'guild_id': int(guild_id),
            'gifs_enabled': enabled is True,
        })

    # Redirect to page
    location = f'/guild_settings?guild_id={guild_id}&gold=1' if post_data['gold'] else f'/guild_settings?guild_id={guild_id}'
    return HTTPFound(location=location)


@routes.post('/set_incest_enabled')
@webutils.requires_login()
async def set_incest_enabled(request:Request):
    """Sets the whether or not incest is enabled for a given guild"""

    # See if they're logged in
    session = await aiohttp_session.get_session(request)
    post_data = await request.post()
    if not session.get('user_id'):
        return HTTPFound(location='/')
    guild_id = post_data['guild_id']
    if not guild_id:
        return HTTPFound(location='/')

    # Get the guilds they're valid to alter
    all_guilds = await webutils.get_user_guilds(request)
    if all_guilds is None:
        return HTTPFound(location='/discord_oauth_login')
    guild = [i for i in all_guilds if (i['owner'] or i['permissions'] & 40 > 0) and guild_id == i['id']]
    if not guild:
        return HTTPFound(location='/')

    # Get the maximum members
    try:
        enabled = bool(post_data['allowed'])
    except (ValueError, KeyError):
        enabled = False

    # Get current prefix
    async with request.app['database']() as db:
        await db('INSERT INTO guild_settings (guild_id, allow_incest) VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET allow_incest=$2', int(guild_id), enabled)
    async with request.app['redis']() as re:
        await re.publish_json('UpdateIncestAllowed', {
            'guild_id': int(guild_id),
            'allow_incest': enabled,
        })

    # Redirect to page
    return HTTPFound(location=f'/guild_settings?guild_id={guild_id}&gold=1')


@routes.post('/set_max_allowed_children')
@webutils.requires_login()
async def set_max_allowed_children(request:Request):
    """Sets the max children for the guild"""

    # See if they're logged in
    session = await aiohttp_session.get_session(request)
    post_data = await request.post()
    if not session.get('user_id'):
        return HTTPFound(location='/')
    guild_id = post_data['guild_id']
    if not guild_id:
        return HTTPFound(location='/')

    # Get the guilds they're valid to alter
    all_guilds = await webutils.get_user_guilds(request)
    if all_guilds is None:
        return HTTPFound(location='/discord_oauth_login')
    guild = [i for i in all_guilds if (i['owner'] or i['permissions'] & 40 > 0) and guild_id == i['id']]
    if not guild:
        return HTTPFound(location='/')

    # Get the maximum members
    hard_maximum_children = max([i['max_children'] for i in request.app['config']['role_perks'].values()])
    hard_minimum_children = min([i['max_children'] for i in request.app['config']['role_perks'].values()])
    max_children_data = {
        int(i): min([max([int(o), hard_minimum_children]), hard_maximum_children]) for i, o in post_data.items() if i.isdigit() and len(o) > 0
    }  # user ID: amount

    # Get current prefix
    async with request.app['database']() as db:
        await db('DELETE FROM max_children_amount WHERE guild_id=$1', int(guild_id))
        for role_id, amount in max_children_data.items():
            await db(
                'INSERT INTO max_children_amount (guild_id, role_id, amount) VALUES ($1, $2, $3)',
                int(guild_id), role_id, amount,
            )
    async with request.app['redis']() as re:
        await re.publish_json('UpdateMaxChildren', {
            'guild_id': int(guild_id),
            'max_children': max_children_data,
        })

    # Redirect to page
    return HTTPFound(location=f'/guild_settings?guild_id={guild_id}&gold=1')


@routes.post('/webhooks/voxel_fox/purchase')
async def paypal_purchase_complete(request:Request):
    """Handles Paypal throwing data my way"""

    # Check the headers
    if request.headers.get("Authorization", None) != request.app['config']['payment_info']['authorization']:
        return Response(status=200)
    data = await request.json()
    custom_data = json.loads(data['custom'])

    async with request.app['database']() as db:
        if data['refunded'] is False:
            await db("INSERT INTO guild_specific_families VALUES ($1, $2) ON CONFLICT (guild_id) DO NOTHING", custom_data['discord_guild_id'], custom_data['discord_user_id'])
        else:
            await db("DELETE FROM guild_specific_families WHERE guild_id=$1", custom_data['discord_guild_id'])

    # Let the user get redirected
    return Response(status=200)


@routes.post('/webhooks/voxel_fox/topgg')
async def webhook_handler(request:Request):
    """Sends a PM to the user with the webhook attached if user in owners"""

    if request.headers.get('Authorization', None) != request.app['config']['topgg_authorization']:
        return Response(400)
    data = await request.json()
    time = dt.utcnow()

    # Send proper thanks to the user
    text = {
        'upvote': 'Thank you for upvoting MarriageBot!',
        'test': 'Thanks for the test ping boss.',
    }.get(data['type'], 'Invalid webhook type from DBL')

    # Redis thanks to user
    async with request.app['redis']() as re:
        await re.publish_json("SendUserMessage", {"user_id": data['user_id'], "content": text})
        await re.publish_json('DBLVote', {'user_id': data['user_id'], 'datetime': time.isoformat()})

    # DB vote
    async with request.app['database']() as db:
        await db('INSERT INTO dbl_votes (user_id, timestamp) VALUES ($1, $2) ON CONFLICT (user_id) DO UPDATE SET timestamp=excluded.timestamp', data['user_id'], time)
    return Response(status=200)


@routes.get('/login_redirect')
async def login_redirect(request:Request):
    """Page the discord login redirects the user to when successfully logged in with Discord"""

    await webutils.process_discord_login(request, ['identify', 'guilds'])
    session = await aiohttp_session.get_session(request)
    return HTTPFound(location=session.pop('redirect_on_login', '/'))
