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
    bot = request.app['bot']
    session = await get_session(request)
    try:
        requested_user_id = requested_user_id or session['user_id']
    except KeyError:
        session.invalidate()
        raise AuthenticationError('No session user ID')

    # Check they're authed to get another user if necessary
    if requested_user_id != session['user_id']:
        # Get the guild from the invite URL in config
        try:
            invite = await bot.fetch_invite(bot.config['guild'])
            support_guild_id = invite.guild.id
        except AttributeError:
            session.invalidate()
            raise AuthenticationError('No support guild URL')

        # Get the members who are allowed the support role
        support_guild = bot.get_guild(support_guild_id)
        bot_admin_role = support_guild.get_role(bot.config['bot_admin_role'])
        if bot_admin_role == None:
            session.invalidate()
            raise AuthenticationError('No valid bot admin role')

        # Checks the users with the support role
        allowed_ids = [i.id for i in bot_admin_role.members]
        if session['user_id'] not in allowed_ids:
            session.invalidate()
            raise AuthenticationError('Not allowed to view page')

    # Returns bot and the user
    return session, bot, bot.get_user(requested_user_id)


@routes.get("/")
@template('index.jinja')
async def index(request:Request):
    '''
    Index of the website
    Has "login with Discord" button
    If not logged in, all pages should redirect here
    '''

    session = await get_session(request)
    bot = request.app['bot']
    login_url = 'https://discordapp.com/api/oauth2/authorize?' + urlencode({
        'client_id': bot.config['oauth']['client_id'],
        'redirect_uri': bot.config['oauth']['redirect_uri'],
        'response_type': 'code',
        'scope': OAUTH_SCOPE
    })
    if not session.get('user'):
        return {'bot': bot, 'user': None, 'login_url': login_url}
    user = session.get('user')
    return HTTPFound(location=f'/colours/{user.id}')


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
    bot = request.app['bot']
    oauth_data = bot.config['oauth']

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
        token_url = f"https://discordapp.com/api/v6/oauth2/token"
        async with session.post(token_url, data=data, headers=headers) as r:
            token_info = await r.json()
        headers.update({
            "Authorization": f"{token_info['token_type']} {token_info['access_token']}"
        })
        user_url = f"https://discordapp.com/api/v6/users/@me"
        async with session.get(user_url, headers=headers) as r:
            user_info = await r.json()
        guilds_url = f"https://discordapp.com/api/v6/users/@me/guilds"
        async with session.get(guilds_url, headers=headers) as r:
            guild_info = await r.json()

    # Save and redirect
    session = await new_session(request)
    session['raw_user_info'] = user_info
    session['user_id'] = user_id = int(user_info['id'])
    session['raw_guild_info'] = guild_info
    return HTTPFound(location=f'/settings/{user_id}')


@routes.get('/settings/{user_id}')
@template('settings.jinja')
async def settings(request:Request):
    '''
    Handles the main settings page for the bot
    '''

    # Get the user
    try:
        session, bot, user = await check_authentication(request, int(request.match_info.get('user_id')))
        if user == None:
            raise AuthenticationError('User does not exist')
    except (ValueError, AuthenticationError) as e:
        return HTTPFound(location='/')

    return {'bot': bot, 'session': session, 'user': user}


@routes.get('/user_settings/{user_id}')
@template('user_settings.jinja')
async def user_settings(request:Request):
    '''
    Handles the users' individual settings pages
    '''

    # Get the user
    try:
        session, bot, user = await check_authentication(request, int(request.match_info.get('user_id')))
        if user == None:
            raise AuthenticationError('User does not exist')
    except (ValueError, AuthenticationError) as e:
        return HTTPFound(location='/')

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
        colours = CustomisedTreeUser.get(user.id).unquoted_hex
    tree_preview_url = '/tree_preview?' + '&'.join([f'{i}={o.strip("#")}' for i, o in colours.items()])
    return {'bot': bot, 'session': session, 'user': user, 'hex_strings': colours, 'tree_preview_url': tree_preview_url}


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

    return {'hex_strings': colours}


@routes.get('/logout')
async def logout(request:Request):
    '''
    Handles logout
    '''
    
    session = await get_session(request)
    session.invalidate()
    return HTTPFound(location='/')
