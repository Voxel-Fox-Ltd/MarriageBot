import json
from datetime import datetime as dt
from urllib.parse import unquote

import aiohttp
import aiohttp_session
import asyncpg
from aiohttp.web import HTTPFound, Request, Response, RouteTableDef

from cogs import utils
from website import utils as webutils

"""
All pages on this website that implement the base.j2 file should return two things:
Firstly, the original request itself under the name 'request'.
Secondly, it should return the user info from the user as gotten from the login under 'user_info'
This is all handled by a decorator below, but I'm just putting it here as a note
"""


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


# @routes.get("/discord_oauth_login/art_contest")
# async def art_contest(request:Request):
#     """Handles redirects using codes stored in the db"""

#     # See if they're logged in
#     await webutils.process_discord_login(request)
#     session = await aiohttp_session.get_session(request)
#     if not session.get('user_id'):
#         return HTTPFound(location='/')
#     url = "https://docs.google.com/forms/d/e/1FAIpQLSdZtfEp7wvzhxy1FpFNxeOhew1zKPTkHMQ7oQ_mla50TRHCrg/viewform?"  # usp=pp_url&entry.865916339={username}&entry.1362434111={user_id}"
#     return HTTPFound(location=url + urlencode({
#         'usp': 'pp_url',
#         'entry.865916339': f"{session['user_info']['username']}#{session['user_info']['discriminator']}",
#         'entry.1362434111': session['user_id'],
#     }))


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


@routes.post('/set_prefix')
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
async def set_max_family_members(request:Request):
    """Sets the maximum family members for a given guild"""

    # See if they're logged in
    post_data = await request.post()
    guild_id = post_data['guild_id']
    if not guild_id:
        return HTTPFound(location='/')

    # Get the guilds they're valid to alter
    all_guilds = await webutils.get_user_guilds(request)
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


@routes.post('/set_incest_enabled')
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
    guild = [i for i in all_guilds if (i['owner'] or i['permissions'] & 40 > 0) and guild_id == i['id']]
    if not guild:
        return HTTPFound(location='/')

    # Get the maximum members
    max_children_data = {int(i): min([max([int(o), 0]), request.app['config']['max_children'][-1]]) for i, o in post_data.items() if i.isdigit() and len(o) > 0}

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


@routes.post('/webhooks/paypal/purchase_ipn')
async def paypal_purchase_complete(request:Request):
    """Handles Paypal throwing data my way"""

    # Get the data
    content_bytes: bytes = await request.content.read()
    paypal_data: str = content_bytes.decode()

    # Send the data back
    data_send_back = "cmd=_notify-validate&" + paypal_data
    async with aiohttp.ClientSession(loop=request.app.loop) as session:
        # paypal_url = "https://ipnpb.sandbox.paypal.com/cgi-bin/webscr"  # Sandbox
        paypal_url = "https://ipnpb.paypal.com/cgi-bin/webscr"  # Live
        async with session.post(paypal_url, data=data_send_back) as site:
            site_data = await site.read()
            if site_data.decode() != "VERIFIED":
                return Response(status=200)  # Oh no it was fake data

    # Get the data from PP
    data_split = {unquote(i.split('=')[0]):unquote(i.split('=')[1]) for i in paypal_data.split('&')}
    custom_data = {i.split('=')[0]:i.split('=')[1] for i in data_split['custom'].split(';')}
    payment_amount = int(data_split['mc_gross'].replace('.', ''))
    print(data_split)

    # Make sure it's real data
    if data_split['receiver_email'] != request.app['config']['paypal_pdt']['receiver_email']:
        return Response(status=200)  # Wrong email passed
    refunded = False
    if payment_amount < 0:
        refunded = True
    elif payment_amount < request.app['config']['payment_info']['original_price'] - request.app['config']['payment_info']['discount_gbp']:
        return Response(status=200)  # Payment too small

    # Database the relevant data
    db_data = {
        'completed': data_split['payment_status'] == 'Completed',
        'checkout_complete_timestamp': dt.utcnow(),
        'customer_id': data_split['payer_id'],
        'id': data_split['txn_id'],
        'payment_amount': payment_amount,
        'discord_id': int(custom_data['user']),
        'guild_id': int(custom_data['guild']),
    }
    if db_data['completed'] is False:
        db_data['checkout_complete_timestamp'] = None
    async with request.app['database']() as db:
        try:
            await db(
                """INSERT INTO paypal_purchases
                (id, customer_id, payment_amount, discord_id, guild_id, completed,
                checkout_complete_timestamp) VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                db_data['id'], db_data['customer_id'], db_data['payment_amount'], db_data['discord_id'],
                db_data['guild_id'], db_data['completed'], db_data['checkout_complete_timestamp'],
            )
        except asyncpg.UniqueViolationError:
            await db(
                """UPDATE paypal_purchases
                SET completed=$1, checkout_complete_timestamp=$2, guild_id=$3, discord_id=$4, customer_id=$5
                WHERE id=$6""",
                db_data['completed'], db_data['checkout_complete_timestamp'], db_data['guild_id'], db_data['discord_id'],
                db_data['customer_id'], db_data['id'],
            )
        if db_data['completed'] is True and refunded is False:
            try:
                await db("INSERT INTO guild_specific_families VALUES ($1)", db_data['guild_id'])
            except asyncpg.UniqueViolationError:
                pass
        if refunded:
            await db("DELETE FROM guild_specific_families WHERE guild_id=$1", db_data['guild_id'])

    # Let the user get redirected
    return Response(status=200)


@routes.get('/webhooks/paypal/return_pdt')
async def paypal_purchase_return(request:Request):
    """Handles Paypal throwing data my way"""

    # Get the data
    transaction_id = request.query['tx']
    data = {
        'tx': transaction_id,
        'at': request.app['config']['paypal_pdt']['identity_token'],
        'cmd': '_notify-synch',
    }

    # Send the data back to PayPal
    async with aiohttp.ClientSession(loop=request.app.loop) as session:
        # paypal_url = "https://www.sandbox.paypal.com/cgi-bin/webscr"  # Sandbox
        paypal_url = "https://www.paypal.com/cgi-bin/webscr"  # Live
        async with session.post(paypal_url, data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'}) as site:
            site_data_bytes = await site.read()
        site_data = site_data_bytes.decode()

    # Work out what we're dealin with
    lines = site_data.strip().split('\n')
    if lines[0] != "SUCCESS":
        return HTTPFound(location='/guild_picker')  # No success

    # Success bois lets GO
    data = {unquote(i.split('=')[0]):unquote(i.split('=')[1]) for i in lines[1:]}
    custom_data = {i.split('=')[0]:i.split('=')[1] for i in request.query['cm'].split(';')}
    payment_amount = int(data['mc_gross'].replace('.', ''))

    # Make sure it's real data
    if data['receiver_email'] != request.app['config']['paypal_pdt']['receiver_email']:
        return Response(status=200)  # Wrong email passed
    if payment_amount < request.app['config']['payment_info']['original_price'] - request.app['config']['payment_info']['discount_gbp']:
        return Response(status=200)  # Payment too small

    # Database the relevant data
    db_data = {
        'completed': data['payment_status'] == 'Completed',
        'checkout_complete_timestamp': dt.utcnow(),
        'customer_id': data['payer_id'],
        'id': data['txn_id'],
        'payment_amount': payment_amount,
        'discord_id': int(custom_data['user']),
        'guild_id': int(custom_data['guild']),
    }
    if db_data['completed'] is False:
        db_data['checkout_complete_timestamp'] = None
    async with request.app['database']() as db:
        try:
            await db(
                """INSERT INTO paypal_purchases
                (id, customer_id, payment_amount, discord_id, guild_id, completed,
                checkout_complete_timestamp) VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                db_data['id'], db_data['customer_id'], db_data['payment_amount'], db_data['discord_id'],
                db_data['guild_id'], db_data['completed'], db_data['checkout_complete_timestamp'],
            )
        except asyncpg.UniqueViolationError:
            await db(
                """UPDATE paypal_purchases
                SET completed=$1, checkout_complete_timestamp=$2, guild_id=$3, discord_id=$4, customer_id=$5
                WHERE id=$6""",
                db_data['completed'], db_data['checkout_complete_timestamp'], db_data['guild_id'], db_data['discord_id'],
                db_data['customer_id'], db_data['id'],
            )
        if db_data['completed'] is True:
            try:
                await db("INSERT INTO guild_specific_families VALUES ($1)", db_data['guild_id'])
            except asyncpg.UniqueViolationError:
                pass

    # Nice, redirect the user
    return HTTPFound(location='/guild_picker')


@routes.post('/webhooks/dbl/vote_added')
async def webhook_handler(request:Request):
    """Sends a PM to the user with the webhook attached if user in owners"""

    # Set up our responses
    success = Response(text=json.dumps({"success": True}), content_type="application/json")

    def failure(data:dict) -> Response:
        return Response(
            text=json.dumps({"success": False, **data}),
            content_type="application/json", status=400
        )

    # See if we can get it
    try:
        x = await request.json()
    except Exception:
        return failure({'reason': 'No JSON response'})

    # See if it's all valid
    keys = set(['bot', 'user', 'type'])
    if not set(x.keys()).issuperset(keys):
        return failure({'reason': 'Invalid request params'})

    # Check the bot's ID
    try:
        if int(x['bot']) != request.app['config']['bot_id']:
            return failure({'reason': 'Invalid bot ID'})  # wrong bot
    except ValueError:
        return failure({'reason': 'Invalid bot ID'})  # not an int

    # Check user's ID
    try:
        user_id = int(x['user'])
    except ValueError:
        return failure({'reason': 'Invalid user ID'})  # uid wasn't int

    # Check type
    if x['type'] not in ['upvote', 'test']:
        return failure({'reason': 'Invalid request type'})

    # Send proper thanks to the user
    if x['type'] == 'upvote':
        text = "Thank you for upvoting MarriageBot!"
    elif x['type'] == 'test':
        text = "Thanks for the test ping boss."
    else:
        text = "Invalid webhook type from DBL"
    time = dt.now()

    # Redis thanks to user
    async with request.app['redis']() as re:
        await re.publish_json("SendUserMessage", {"user_id": user_id, "content": text})
        await re.publish_json('DBLVote', {'user_id': user_id, 'datetime': time.isoformat()})

    # DB vote
    async with request.app['database']() as db:
        try:
            await db('INSERT INTO dbl_votes (user_id, timestamp) VALUES ($1, $2)', user_id, time)
        except asyncpg.UniqueViolationError:
            await db('UPDATE dbl_votes SET timestamp=$2 WHERE user_id=$1', user_id, time)
    return success


@routes.get('/login_redirect')
async def login_redirect(request:Request):
    """Page the discord login redirects the user to when successfully logged in with Discord"""

    await aiohttp_session.new_session(request)
    await webutils.process_discord_login(request, ['identify', 'guilds'])
    return HTTPFound(location=f'/')
