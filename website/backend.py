import aiohttp_session
from aiohttp.web import HTTPFound, Request, RouteTableDef

from website import utils as webutils

routes = RouteTableDef()


@routes.get('/login_redirect')
async def login(request:Request):
    """Page the discord login redirects the user to when successfully logged in with Discord"""

    await webutils.process_discord_login(request, ['identify', 'guilds'])
    session = await aiohttp_session.get_session(request)
    return HTTPFound(location=session.pop('redirect_on_login', '/'))
