import os
from urllib.parse import urlencode
import functools

import aiohttp
from aiohttp.web import RouteTableDef, Request, HTTPFound, static, Response
import aiohttp_session
from aiohttp_jinja2 import template
import json
import discord

from cogs import utils


"""
All pages on this website that implement the base.jinja file should return two things:
Firstly, the original request itself under the name 'request'.
Secondly, it should return the user info from the user as gotten from the login under 'user_info'
This is all handled by a decorator below, but I'm just putting it here as a note
"""


routes = RouteTableDef()
OAUTH_SCOPES = 'identify guilds'


def add_output_args(*, redirect_if_logged_out:str=None, redirect_if_logged_in:str=None):
    """This function is a wrapper around all routes. It takes the output and
    adds the user info and request to the returning dictionary
    It must be applied before the template decorator"""

    def inner_wrapper(func):
        """An inner wrapper so I can get args at the outer level"""

        async def wrapper(request:Request):
            """This is the wrapper that does all the heavy lifting"""

            # Run function
            data = await func(request)

            # See if we return anything other than data (like redirects)
            if not isinstance(data, dict):
                return data

            # Update data with the information
            if data is None:
                data = dict()
            session = await aiohttp_session.get_session(request)
            try:
                data.update({'user_info': session['user_info']})
            except KeyError:
                data.update({'user_info': None})
            data.update({'request': request})

            # Check return relevant info
            if redirect_if_logged_out and session.get('user_id') is None:
                return HTTPFound(location=redirect_if_logged_out)
            elif redirect_if_logged_in and session.get('user_id') is not None:
                return HTTPFound(location=redirect_if_logged_in)
            return data
        return wrapper
    return inner_wrapper


def get_avatar(user_info:dict=dict()):
    """Gets the avatar URL for a user when provided with their user info
    If no arguments are provided then the default Discord avatar is given"""

    try:
        return f"https://cdn.discordapp.com/avatars/{user_info['id']}/{user_info['avatar']}.png"
    except KeyError:
        try:
            return f"https://cdn.discordapp.com/embed/avatars/{int(user_info['discriminator']) % 5}.png"
        except KeyError:
            pass
    return "https://cdn.discordapp.com/embed/avatars/0.png"


@routes.get("/")
@template('index.jinja')
@add_output_args(redirect_if_logged_in="/settings")
async def index(request:Request):
    """Index of the website, has "login with Discord" button
    If not logged in, all pages should redirect here"""

    config = request.app['config']
    login_url = 'https://discordapp.com/api/oauth2/authorize?' + urlencode({
        'client_id': config['oauth']['client_id'],
        'redirect_uri': config['oauth']['redirect_uri'],
        'response_type': 'code',
        'scope': OAUTH_SCOPES
    })
    return {'login_url': login_url}


@routes.get("/reset2019")
@template('blog.jinja')
@add_output_args()
async def reset(request:Request):
    """The lol blog post that was sent out when MB was reset back in July 2019"""

    config = request.app['config']
    login_url = 'https://discordapp.com/api/oauth2/authorize?' + urlencode({
        'client_id': config['oauth']['client_id'],
        'redirect_uri': config['oauth']['redirect_uri'],
        'response_type': 'code',
        'scope': OAUTH_SCOPES
    })
    return {'login_url': login_url}


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
    user_info['avatar_link'] = get_avatar(user_info)
    session['user_info'] = user_info
    session['guild_info'] = guild_info
    session['user_id'] = int(user_info['id'])

    # Redirect to settings
    return HTTPFound(location=f'/settings')


@routes.get('/settings')
@template('settings.jinja')
@add_output_args(redirect_if_logged_out="/")
async def settings(request:Request):
    """Handles the main settings page for the bot"""

    # See if they're logged in
    session = await aiohttp_session.get_session(request)
    if not session.get('user_id'):
        return HTTPFound(location='/')

    # Give them the page
    return {
        'user_info': session['user_info'], 'request': request,
    }


@routes.get('/user_settings')
@template('user_settings.jinja')
@add_output_args(redirect_if_logged_out="/")
async def user_settings(request:Request):
    """Handles the users' individual settings pages"""

    # See if they're logged in
    session = await aiohttp_session.get_session(request)
    if not session.get('user_id'):
        return HTTPFound(location='/')

    # Get the colours they're using
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
        async with request.app['database']() as db:
            data = await db('SELECT * FROM customisation WHERE user_id=$1', session['user_id'])
        try:
            colours = utils.CustomisedTreeUser(**data[0]).unquoted_hex
        except (IndexError, TypeError):
            colours = utils.CustomisedTreeUser.get_default_unquoted_hex()

    # Make a URL for the preview
    tree_preview_url = '/tree_preview?' + '&'.join([f'{i}={o.strip("#")}' if i != 'direction' else f'{i}={o}' for i, o in colours.items()])

    # Give all the data to the page
    return {
        'user_info': session['user_info'],
        'hex_strings': colours,
        'tree_preview_url': tree_preview_url,
        'request': request,
    }


@routes.post('/user_settings')
async def user_settings_post_handler(request:Request):
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


@routes.get('/tree_preview')
@template('tree_preview.jinja')
@add_output_args()
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
@add_output_args(redirect_if_logged_out="/")
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
    return {
        'user_info': session['user_info'],
        'guilds': guilds,
        'request': request,
    }


@routes.get('/guild_settings')
@template('guild_settings.jinja')
@add_output_args(redirect_if_logged_out="/")
async def guild_settings_get(request:Request):
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

    # Get current prefix
    async with request.app['database']() as db:
        prefix = await db('SELECT prefix FROM guild_settings WHERE guild_id=$1', int(guild_id))
    try:
        prefix = prefix[0]['prefix']
    except IndexError:
        prefix = request.app['config']['prefix']['default_prefix']

    # Get channels
    try:
        guild_object = await request.app['bot'].fetch_guild(int(guild_id))
        channels = sorted([i for i in await guild_object.fetch_channels() if isinstance(i, discord.TextChannel)], key=lambda c: c.position)
    except Exception:
        channels = []

    # Return info to the page
    return {
        'user_info': session['user_info'],
        'guild': guild[0],
        'prefix': prefix,
        'channels': channels,
        'request': request,
    }


@routes.post('/guild_settings')
@template('guild_settings.jinja')
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


@routes.get('/logout')
async def logout(request:Request):
    """Handles logout"""

    session = await aiohttp_session.get_session(request)
    session.invalidate()
    return HTTPFound(location='/')
