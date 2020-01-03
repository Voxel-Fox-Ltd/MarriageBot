import aiohttp
from aiohttp.web import RouteTableDef, Request, HTTPFound, Response
import aiohttp_session

from website.utils.get_avatar import get_avatar


OAUTH_SCOPES = 'identify guilds guilds.join'
DISCORD_OAUTH_URL = 'https://discordapp.com/api/oauth2/authorize?'


async def process_discord_login(request:Request):
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
        'scope': OAUTH_SCOPES
    }
    data.update(oauth_data)
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

        # Add to guild
        guild_join_url = f"https://discordapp.com/api/v6/guilds/{config['guild_id']}/members/{user_info['id']}"
        bot_headers = {'Authorization': f"Bot {config['token']}"}
        async with session.put(guild_join_url, headers=bot_headers, json={'access_token': token_info['access_token']}) as r:
            print(await r.read())
            print(r.status)

    # Save to session
    session = await aiohttp_session.new_session(request)
    user_info['avatar_link'] = get_avatar(user_info)
    session['user_info'] = user_info
    session['guild_info'] = guild_info
    session['user_id'] = int(user_info['id'])
