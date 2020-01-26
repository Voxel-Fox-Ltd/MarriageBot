import asyncio
from urllib.parse import urlencode

import aiohttp
import aiohttp_session
from aiohttp.web import HTTPFound, Request

from website.utils.get_avatar import get_avatar

DISCORD_OAUTH_URL = 'https://discordapp.com/api/oauth2/authorize?'


def get_discord_login_url(request:Request, redirect_uri:str, oauth_scopes:list=None):
    """Get a valid URL for a user to use to login to the website"""

    config = request.app['config']
    oauth_data = config['oauth']
    oauth_scopes = oauth_scopes or ["identify", "guilds"]
    return DISCORD_OAUTH_URL + urlencode({
        'redirect_uri': redirect_uri,
        'scope': ' '.join(oauth_scopes),
        'response_type': 'code',
        'client_id': oauth_data['client_id'],
    })


async def process_discord_login(request:Request, oauth_scopes:list=None):
    """Process the login from Discord and store relevant data in the session"""

    # Get the code
    code = request.query.get('code')
    if not code:
        return HTTPFound(location='/')

    # Get the bot
    config = request.app['config']
    oauth_data = config['oauth']

    # Generate the post data
    oauth_scopes = oauth_scopes or ["identify", "guilds"]
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'scope': ' '.join(oauth_scopes),
        **oauth_data,
    }
    if request.url.explicit_port:
        data['redirect_uri'] = "http://{0.host}:{0.port}{0.path}".format(request.url)
    else:
        data['redirect_uri'] = "https://{0.host}{0.path}".format(request.url)
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    # Make session so we can do stuff with it
    session_storage = await aiohttp_session.get_session(request)

    # Make the request
    async with aiohttp.ClientSession(loop=request.loop) as session:

        # Get auth
        token_url = f"https://discordapp.com/api/v6/oauth2/token"
        async with session.post(token_url, data=data, headers=headers) as r:
            token_info = await r.json()
        if token_info.get('error'):
            return  # Error getting the token, just ignore it

        # Update headers
        headers.update({
            "Authorization": f"{token_info['token_type']} {token_info['access_token']}"
        })
        session_storage['token_info'] = token_info

        # Get user
        if "identify" in oauth_scopes:
            user_url = f"https://discordapp.com/api/v6/users/@me"
            async with session.get(user_url, headers=headers) as r:
                user_info = await r.json()
            user_info['avatar_url'] = get_avatar(user_info)
            session_storage['user_info'] = user_info
            session_storage['user_id'] = int(user_info['id'])
            session_storage['logged_in'] = True


async def get_user_guilds(request:Request):
    """Process the login from Discord and store relevant data in the session"""

    # Get auth
    session_storage = await aiohttp_session.get_session(request)
    token_info = session_storage['token_info']
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'{token_info["token_type"]} {token_info["access_token"]}'
    }

    # Make the request
    async with aiohttp.ClientSession(loop=request.loop) as session:

        # Get guilds
        guilds_url = f"https://discordapp.com/api/v6/users/@me/guilds"
        while True:
            async with session.get(guilds_url, headers=headers) as r:
                guild_info = await r.json()
                if r.status == 429:
                    await asyncio.sleep(guild_info['retry_after'] / 1000)
                    continue
                break

    return guild_info
