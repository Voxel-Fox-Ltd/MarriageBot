from os import getcwd
from json import dumps
from urllib.parse import urlencode

from aiohttp import ClientSession
from aiohttp.web import RouteTableDef, Request, HTTPFound, static, Response
from aiohttp_session import new_session, get_session
from aiohttp_jinja2 import template

from cogs.utils.customised_tree_user import CustomisedTreeUser


routes = RouteTableDef()
OAUTH_SCOPE = 'identify guilds'


class AuthenticationError(Exception):
    '''Raised to show that they don't have any authentication'''
    def __init__(self, message:str):
        super().__init__(message)


async def check_authentication(request:Request, requested_user_id:int=None):
    '''
    Checks if the session user is both logged in and is allowed to get the requested user
    '''

    # Get main vairables
    session = await get_session(request)
    try:
        requested_user_id = requested_user_id or session['user_id']
        if requested_user_id == None:
            raise KeyError
    except KeyError:
        session.invalidate()
        raise AuthenticationError('No session user ID')

    # Check they're authed to get another user if necessary
    if requested_user_id != session['user_id']:
        # Get the guild from the invite URL in config
        # try:
        #     # TODO get support guild ID
        # except AttributeError:
        #     session.invalidate()
        #     raise AuthenticationError('No support guild URL')

        # # Get the members who are allowed the support role
        # # TODO get support guild role - check permissions in guild?
        # if bot_admin_role == None:
        #     session.invalidate()
        #     raise AuthenticationError('No valid bot admin role')

        # # Checks the users with the support role
        # # TODO check for bot admin role on user
        # if session['user_id'] not in allowed_ids:
        #     session.invalidate()
        #     raise AuthenticationError('Not allowed to view page')
        raise AuthenticationError("I'll deal with this later")

    # Returns bot and the user
    return session, bot


def get_avatar(user_info:dict=dict()):
    '''Gets the avatar URL for a given user'''

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
async def index(request:Request):
    '''
    Index of the website
    Has "login with Discord" button
    If not logged in, all pages should redirect here
    '''

    session = await get_session(request)
    config = request.app['config']
    login_url = 'https://discordapp.com/api/oauth2/authorize?' + urlencode({
        'client_id': config['oauth']['client_id'],
        'redirect_uri': config['oauth']['redirect_uri'],
        'response_type': 'code',
        'scope': OAUTH_SCOPE
    })
    if not session.get('user_id'):
        return {
            'user_info': None, 
            'login_url': login_url
        }
    return HTTPFound(location=f"/settings")


@routes.get('/login')
async def login(request:Request):
    '''
    Page the discord login redirects the user to when successfully logged in with Discord
    '''

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
        'scope': OAUTH_SCOPE
    }
    data.update(oauth_data)
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    # Make the request
    async with ClientSession(loop=request.loop) as session:

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
    session = await new_session(request)

    # Update avatar data
    user_info['avatar_link'] = get_avatar(user_info)
    session['user_info'] = user_info

    # Update guild data
    session['guild_info'] = guild_info

    # Redirect to settings
    session['user_id'] = int(user_info['id'])
    print(session)
    return HTTPFound(location=f'/settings')


@routes.get('/settings')
@template('settings.jinja')
async def settings(request:Request):
    '''
    Handles the main settings page for the bot
    '''

    # See if they're logged in
    session = await get_session(request)
    print(session)
    if not session.get('user_id'):
        return HTTPFound(location='/')

    # Give them the page
    return {
        'user_info': session['user_info'], 
    }


@routes.get('/user_settings')
@template('user_settings.jinja')
async def user_settings(request:Request):
    '''
    Handles the users' individual settings pages
    '''

    # See if they're logged in
    session = await get_session(request)
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
            colours = CustomisedTreeUser(**data[0]).unquoted_hex
        except (IndexError, TypeError):
            colours = CustomisedTreeUser.get_default_unquoted_hex()

    # Make a URL for the preview
    tree_preview_url = '/tree_preview?' + '&'.join([f'{i}={o.strip("#")}' for i, o in colours.items()])

    # Give all the data to the page
    return {
        'user_info': session['user_info'],
        'hex_strings': colours, 
        'tree_preview_url': tree_preview_url,
    }


@routes.get('/tree_preview')
@template('tree_preview.jinja')
async def tree_preview(request:Request):
    '''
    Tree preview for the bot
    '''

    colours_raw = {
        'edge': request.query.get('edge'),
        'node': request.query.get('node'),
        'font': request.query.get('font'),
        'highlighted_font': request.query.get('highlighted_font'),
        'highlighted_node': request.query.get('highlighted_node'),
        'background': request.query.get('background'),
    } 
    colours = {}
    for i, o in colours_raw.items():
        if o == None or o == 'transparent':
            o = 'transparent'
        else:
            o = f'#{o.strip("#")}'
        colours[i] = o

    return {
        'hex_strings': colours,
    }


@routes.get('/logout')
async def logout(request:Request):
    '''
    Handles logout
    '''
    
    session = await get_session(request)
    session.invalidate()
    return HTTPFound(location='/')
