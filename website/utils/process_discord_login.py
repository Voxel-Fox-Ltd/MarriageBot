import aiohttp
from aiohttp.web import RouteTableDef, Request, HTTPFound, Response
import aiohttp_session

from website.utils.get_avatar import get_avatar


DISCORD_OAUTH_URL = 'https://discordapp.com/api/oauth2/authorize?'


async def process_discord_login(request:Request, oauth_scopes:list=list("identify", "guilds"), *, https:bool=True):
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
    }
    data.update(oauth_data)
    data['redirect_uri'] = "http{0}://{1.host}{1.path}".format('s' if https else '', request.url)
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    # Make session so we can do stuff with it
    session = await aiohttp_session.new_session(request)

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
        if "identify" in oauth_scopes:
            user_url = f"https://discordapp.com/api/v6/users/@me"
            async with session.get(user_url, headers=headers) as r:
                user_info = await r.json()
            user_info['avatar_link'] = get_avatar(user_info)
            session['user_info'] = user_info
            session['user_id'] = int(user_info['id'])

        # Get guilds
        if "guilds" in oauth_scopes:
            guilds_url = f"https://discordapp.com/api/v6/users/@me/guilds"
            async with session.get(guilds_url, headers=headers) as r:
                guild_info = await r.json()
            session['guild_info'] = guild_info
