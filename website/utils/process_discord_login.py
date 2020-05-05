import asyncio
from urllib.parse import urlencode
from datetime import datetime as dt, timedelta

import aiohttp
import aiohttp_session
from aiohttp.web import HTTPFound, Request

from website.utils.get_avatar_url import get_avatar_url


DISCORD_OAUTH_URL = 'https://discordapp.com/api/oauth2/authorize?'


def get_discord_login_url(request:Request, redirect_uri:str, oauth_scopes:list=None):
    """Get a valid URL for a user to use to login to the website"""

    config = request.app['config']
    oauth_data = config['oauth']
    return DISCORD_OAUTH_URL + urlencode({
        'redirect_uri': redirect_uri,
        'scope': ' '.join(oauth_scopes),
        'response_type': 'code',
        'client_id': oauth_data['client_id'],
    })


async def process_discord_login(request:Request, oauth_scopes:list):
    """Process the login from Discord and store relevant data in the session"""

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
            "Authorization": f"Bearer {token_info['access_token']}"
        })
        token_info['expires_at'] = (dt.utcnow() + timedelta(seconds=token_info['expires_in'])).timestamp()
        updated_token_info = session_storage.get('token_info', dict())
        updated_token_info.update(token_info)
        session_storage['token_info'] = updated_token_info

    # Get user
    if "identify" in oauth_scopes:
        await get_user_info(request, refresh=True)


async def get_user_info(request:Request, *, refresh:bool=False):
    """Get the user's info"""

    session_storage = await aiohttp_session.get_session(request)
    if refresh is False:
        return session_storage['user_info']
    user_url = f"https://discordapp.com/api/v6/users/@me"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    headers.update({
        "Authorization": f"Bearer {session_storage['token_info']['access_token']}"
    })
    async with aiohttp.ClientSession(loop=request.loop) as session:
        async with session.get(user_url, headers=headers) as r:
            user_info = await r.json()
    user_info['avatar_url'] = get_avatar_url(user_info)
    session_storage['user_info'] = user_info
    session_storage['user_id'] = int(user_info['id'])
    session_storage['logged_in'] = True
    return user_info


async def get_access_token(request:Request, oauth_scopes:list=None, *, refresh_if_expired:bool=True, refresh:bool=False) -> str:
    """Get the access token for a given user"""

    # Get relevant data
    session_storage = await aiohttp_session.get_session(request)
    config = request.app['config']
    oauth_data = config['oauth']

    # See if we even need to make a new request
    if refresh:
        pass
    elif refresh_if_expired is False or session_storage['token_info']['expires_at'] < dt.utcnow().timestamp():
        return session_storage['token_info']['access_token']

    # Generate the post data
    data = {
        'grant_type': 'refresh_token',
        'scope': ' '.join(oauth_scopes or session_storage['token_info']['scope']),
        **oauth_data,
    }
    if request.url.explicit_port:
        data['redirect_uri'] = "http://{0.host}:{0.port}{0.path}".format(request.url)
    else:
        data['redirect_uri'] = "https://{0.host}{0.path}".format(request.url)
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    # Make the request
    async with aiohttp.ClientSession(loop=request.loop) as session:

        # Get auth
        token_url = f"https://discordapp.com/api/v6/oauth2/token"
        async with session.post(token_url, data=data, headers=headers) as r:
            token_info = await r.json()
        if token_info.get('error'):
            return ""  # Error getting the token, just ignore it, TODO raise something

    # Store data
    token_info['expires_at'] = (dt.utcnow() + timedelta(seconds=token_info['expires_in'])).timestamp()
    updated_token_info = session_storage['token_info']
    updated_token_info.update(token_info)
    session_storage['token_info'] = updated_token_info
    return updated_token_info['access_token']


async def get_user_guilds(request:Request):
    """Process the login from Discord and store relevant data in the session"""

    # Get auth
    session_storage = await aiohttp_session.get_session(request)
    try:
        token_info = session_storage['token_info']
    except KeyError:
        return None
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Bearer {token_info["access_token"]}'
    }

    # Make the request
    async with aiohttp.ClientSession(loop=request.loop) as session:
        guilds_url = f"https://discordapp.com/api/v6/users/@me/guilds"

        # Loop until success
        while True:
            async with session.get(guilds_url, headers=headers) as r:
                guild_info = await r.json()

                # Rate limit? Just wait
                if r.status == 429:
                    await asyncio.sleep((guild_info['retry_after'] / 1000) + 0.5)
                    continue

                # We fucked up elsewhere? Just leave
                elif str(r.status)[0] in ['4', '5']:
                    return []

                # Oh boye we done
                break

    # Return guild info
    return guild_info


async def add_user_to_guild(request:Request, guild_id:int) -> bool:
    """Adds the user to the given guild (if the correct scopes were previously provided)
    Returns a boolean of whether or not that user was added (or was already in the guild) successfully"""

    # Get the bot
    session_storage = await aiohttp_session.get_session(request)
    user_info = session_storage['user_info']
    token_info = session_storage['token_info']

    # Get our headers
    guild_join_url = f"https://discordapp.com/api/v6/guilds/{guild_id}/members/{user_info['id']}"
    headers = {'Authorization': f"Bot {request.app['config']['token']}"}

    # Get our access token
    data = {
        'access_token': await get_access_token(request)
    }

    # Make the request
    async with aiohttp.ClientSession(loop=request.loop) as session:
        async with session.put(guild_join_url, headers=headers, json=data) as r:
            return str(r.status)[0] == '2'  # 201 - Added, 204 - Already in the guild
