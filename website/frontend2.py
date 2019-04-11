from os import getcwd
from json import dumps

from aiohttp import ClientSession
from aiohttp.web import RouteTableDef, Request, HTTPFound, static, Response
from aiohttp_session import new_session, get_session
from aiohttp_jinja2 import template

from cogs.utils.customised_tree_user import CustomisedTreeUser


routes = RouteTableDef()


@routes.get("/")
@template('index.jinja')
async def index(request:Request):
    '''
    Index of the website
    Has "login with Discord" button
    If not logged in, all pages should redirect here
    '''

    session = await get_session(request)
    if not session.get('user'):
        return {'bot': request.app['bot'], 'user': None}
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
        'scope': 'identify guilds',
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
    session['user_info'] = user_info
    session['user'] = user = bot.get_user(int(user_info['id']))
    session['guild_info'] = guild_info
    return HTTPFound(location=f'/colours/{user.id}')
