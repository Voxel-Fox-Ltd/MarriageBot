from urllib.parse import urlencode

import aiohttp
from aiohttp.web import RouteTableDef, Request, HTTPFound
import aiohttp_session
from aiohttp_jinja2 import template
import discord

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


@routes.get("/")
@template('index.jinja')
@webutils.add_output_args(redirect_if_logged_in="/settings")
async def index(request:Request):
    """Index of the website, has "login with Discord" button
    If not logged in, all pages should redirect here"""

    config = request.app['config']
    login_url = DISCORD_OAUTH_URL + urlencode({
        'client_id': config['oauth']['client_id'],
        'redirect_uri': config['oauth']['redirect_uri'],
        'response_type': 'code',
        'scope': OAUTH_SCOPES
    })
    return {'login_url': login_url}


@routes.get("/blog/{code}")
@template('blog.jinja')
@webutils.add_output_args()
async def blog(request:Request):
    """Blog post handler"""

    url_code = request.match_info['code']
    async with request.app['database']() as db:
        data = await db("SELECT * FROM blog_posts WHERE url=$1", url_code)
    if not data:
        return {'title': 'Post not found'}
    text = data[0]['body'].split('\n')
    return {
        'text': webutils.text_to_html(text),
        'title': data[0]['title'],
        'opengraph': {
            'article:published_time': data[0]['created_at'].isoformat(),
            'article:modified_time': data[0]['created_at'].isoformat(),
            'og:type': 'article',
            'og:title': f"MarriageBot - {data[0]['title']}",
            'og:description': text[0],
        }
    }


@routes.get('/settings')
@template('settings.jinja')
@webutils.add_output_args(redirect_if_logged_out="/r/login")
async def settings(request:Request):
    """Handles the main settings page for the bot"""

    # See if they're logged in
    session = await aiohttp_session.get_session(request)
    if not session.get('user_id'):
        return HTTPFound(location='/')

    # Give them the page
    return {}


@routes.get('/user_settings')
@template('user_settings.jinja')
@webutils.add_output_args(redirect_if_logged_out="/r/login")
async def user_settings(request:Request):
    """Handles the users' individual settings pages"""

    # See if they're logged in
    session = await aiohttp_session.get_session(request)
    if not session.get('user_id'):
        return HTTPFound(location='/')

    # Get the colours they're using
    db = await request.app['database'].get_connection()
    if len(request.query) > 0:
        colours_raw = {
            'edge': request.query.get('edge'),
            'node': request.query.get('node'),
            'font': request.query.get('font'),
            'highlighted_font': request.query.get('highlighted_font'),
            'highlighted_node': request.query.get('highlighted_node'),
            'background': request.query.get('background'),
            'direction': request.query.get('direction', 'TB'),
        }
        colours = {}
        for i, o in colours_raw.items():
            if o == None:
                o = 'transparent'
            colours[i] = o
    else:
        data = await db('SELECT * FROM customisation WHERE user_id=$1', session['user_id'])
        try:
            colours = utils.CustomisedTreeUser(**data[0]).unquoted_hex
        except (IndexError, TypeError):
            colours = utils.CustomisedTreeUser.get_default_unquoted_hex()

    # Make a URL for the preview
    tree_preview_url = '/tree_preview?' + '&'.join([f'{i}={o.strip("#")}' if i != 'direction' else f'{i}={o}' for i, o in colours.items()])

    # Get their blocked users
    blocked_users_db = await db("SELECT blocked_user_id FROM blocked_user WHERE user_id=$1", session['user_id'])
    blocked_users = {i['blocked_user_id']: await request.app['bot'].get_name(i['blocked_user_id']) for i in blocked_users_db}

    # Give all the data to the page
    await db.disconnect()
    return {
        'hex_strings': colours,
        'tree_preview_url': tree_preview_url,
        'blocked_users': blocked_users,
    }


@routes.get('/tree_preview')
@template('tree_preview.jinja')
@webutils.add_output_args()
async def tree_preview(request:Request):
    """Tree preview for the bot"""

    colours_raw = {
        'edge': request.query.get('edge'),
        'node': request.query.get('node'),
        'font': request.query.get('font'),
        'highlighted_font': request.query.get('highlighted_font'),
        'highlighted_node': request.query.get('highlighted_node'),
        'background': request.query.get('background'),
        'direction': request.query.get('direction'),
    }
    colours = {}
    for i, o in colours_raw.items():
        if o == None or o == 'transparent':
            o = 'transparent'
        elif i == 'direction':
            pass
        else:
            o = f'#{o.strip("#")}'
        colours[i] = o

    return {
        'hex_strings': colours,
    }


@routes.get('/guild_picker')
@template('guild_picker.jinja')
@webutils.add_output_args(redirect_if_logged_out="/r/login")
async def guild_picker(request:Request):
    """Shows the guilds that the user has permission to change"""

    # See if they're logged in
    session = await aiohttp_session.get_session(request)
    if not session.get('user_id'):
        return HTTPFound(location='/')

    # Get the guilds they're valid to alter
    all_guilds = session['guild_info']
    try:
        guilds = [i for i in all_guilds if i['owner'] or i['permissions'] & 40 > 0]
    except TypeError:
        # No guilds provided - did they remove the scope? who knows
        guilds = []

    # Get the guilds that have gold
    guild_ids = [int(i['id']) for i in guilds]
    async with request.app['database']() as db:
        gold_guild_data = await db("SELECT * FROM guild_specific_families WHERE guild_id=ANY($1::BIGINT[])", guild_ids)
    gold_guild_ids = [str(i['guild_id']) for i in gold_guild_data]
    for i in guilds:
        if i['id'] in gold_guild_ids:
            i['gold'] = True
        else:
            i['gold'] = False

    return {'guilds': guilds}


@routes.get('/guild_settings')
@template('guild_settings.jinja')
@webutils.add_output_args(redirect_if_logged_out="/r/login")
async def guild_settings_get(request:Request):
    """Shows the settings for a particular guild"""

    # See if they're logged in
    session = await aiohttp_session.get_session(request)
    if not session.get('user_id'):
        return HTTPFound(location='/')
    guild_id = request.query.get('guild_id')
    if not guild_id:
        return HTTPFound(location='/')

    # See if the bot is in the guild
    bot = request.app['bot']
    try:
        guild_object = await bot.fetch_guild(int(guild_id))
    except discord.Forbidden:
        config = request.app['config']
        location = DISCORD_OAUTH_URL + urlencode({
            'client_id': config['oauth']['client_id'],
            'redirect_uri': config['oauth']['join_server_redirect_uri'], # + f'?guild_id={guild_id}',
            'response_type': 'code',
            'permissions': 52224,
            'scope': 'bot',
            'guild_id': guild_id,
        })
        return HTTPFound(location=location)

    # Get the guilds they're valid to alter
    all_guilds = session['guild_info']
    oauth_guild_data = [i for i in all_guilds if (i['owner'] or i['permissions'] & 40 > 0) and guild_id == i['id']]
    if not oauth_guild_data:
        return HTTPFound(location='/')

    # Get current prefix
    async with request.app['database']() as db:
        guild_settings = await db('SELECT * FROM guild_settings WHERE guild_id=$1', int(guild_id))
        mbg = await db('SELECT * FROM guild_specific_families WHERE guild_id=$1', int(guild_id))
    try:
        prefix = guild_settings[0]['prefix']
    except IndexError:
        prefix = request.app['config']['prefix']['default_prefix']

    # Get channels
    channels = sorted([i for i in await guild_object.fetch_channels() if isinstance(i, discord.TextChannel)], key=lambda c: c.position)

    # Return info to the page
    return {
        'guild': guild_object,
        'prefix': prefix,
        'channels': channels,
        'gold': bool(mbg),
        'normal': None,
    }


@routes.get('/guild_gold_settings')
@template('guild_settings.jinja')
@webutils.add_output_args(redirect_if_logged_out="/r/login")
async def guild_gold_settings_get(request:Request):
    """Shows the settings for a particular guild"""

    # See if they're logged in
    session = await aiohttp_session.get_session(request)
    if not session.get('user_id'):
        return HTTPFound(location='/')
    guild_id = request.query.get('guild_id')
    if not guild_id:
        return HTTPFound(location='/')

    # See if the bot is in the guild
    bot = request.app['gold_bot']
    try:
        guild_object = await bot.fetch_guild(int(guild_id))
    except discord.Forbidden:
        config = request.app['gold_config']
        location = DISCORD_OAUTH_URL + urlencode({
            'client_id': config['oauth']['client_id'],
            'redirect_uri': config['oauth']['join_server_redirect_uri'], # + f'?guild_id={guild_id}',
            'response_type': 'code',
            'permissions': 52224,
            'scope': 'bot',
            'guild_id': guild_id,
        })
        return HTTPFound(location=location)

    # See if non-gold is in the guild
    non_gold_bot = request.app['bot']
    try:
        guild_object = await non_gold_bot.fetch_guild(int(guild_id))
        non_gold_in_guild = True
    except discord.Forbidden:
        non_gold_in_guild = False

    # Get the guilds they're valid to alter
    all_guilds = session['guild_info']
    oauth_guild_data = [i for i in all_guilds if (i['owner'] or i['permissions'] & 40 > 0) and guild_id == i['id']]
    if not oauth_guild_data:
        return HTTPFound(location='/')

    # Get current prefix
    async with request.app['database']() as db:
        guild_settings = await db('SELECT * FROM guild_settings WHERE guild_id=$1', int(guild_id))
    try:
        prefix = guild_settings[0]['gold_prefix']
    except IndexError:
        prefix = request.app['gold_config']['prefix']['default_prefix']

    # Get channels
    channels = sorted([i for i in await guild_object.fetch_channels() if isinstance(i, discord.TextChannel)], key=lambda c: c.position)

    # Return info to the page
    return {
        'guild': guild_object,
        'prefix': prefix,
        'channels': channels,
        'gold': None,
        'normal': non_gold_in_guild,
    }


@routes.get('/buy_gold')
@template('buy_gold.jinja')
@webutils.add_output_args(redirect_if_logged_out="/r/login")
async def buy_gold(request:Request):
    """Shows the guilds that the user has permission to change"""

    # Get relevant data
    session = await aiohttp_session.get_session(request)
    guild_id = request.query.get('guild_id')
    if not guild_id:
        return HTTPFound(location='/guild_picker')
    guild_id = int(guild_id)

    # Generate params
    data = {
        "payment_method_types[0]": "card",
        "success_url": f"https://marriagebot.xyz/guild_settings?guild_id={guild_id}",
        "cancel_url": f"https://marriagebot.xyz/guild_settings?guild_id={guild_id}",
        "line_items[0][name]": 'MarriageBot Gold',
        "line_items[0][description]": f"Access to the Discord bot 'MarriageBot Gold' for guild ID {guild_id}" + {
            True: f"(Discounted by £{request.app['config']['stripe']['discount_gpb']/100:.2f})",
            False: ""
        }[request.app['config']['stripe']['discount_gpb'] > 0],
        "line_items[0][amount]": 2000 - request.app['config']['stripe']['discount_gpb'],
        "line_items[0][currency]": 'gbp',
        "line_items[0][quantity]": 1,
    }
    url = "https://api.stripe.com/v1/checkout/sessions"

    # Send request
    async with aiohttp.ClientSession(loop=request.app.loop) as requests:
        async with requests.post(url, data=data, auth=aiohttp.BasicAuth(request.app['config']['stripe']['secret_key'])) as r:
            stripe_session = await r.json()

    # Store data
    async with request.app['database']() as db:
        await db(
            "INSERT INTO stripe_purchases (id, name, payment_amount, discord_id, guild_id) VALUES ($1, $2, $3, $4, $5)",
            stripe_session['id'], stripe_session['display_items'][0]['custom']['name'],
            stripe_session['display_items'][0]['amount'], session['user_id'], guild_id
        )

    # Return relevant info to page
    return {
        'stripe_publishable_key': request.app['config']['stripe']['public_key'],
        'checkout_session_id': stripe_session['id'],
    }


@routes.get('/logout')
async def logout(request:Request):
    """Handles logout"""

    session = await aiohttp_session.get_session(request)
    session.invalidate()
    return HTTPFound(location='/')
