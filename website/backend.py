from aiohttp.web import RouteTableDef, Request, HTTPFound, Response

from website import utils as webutils


routes = RouteTableDef()


@routes.get('/login_redirect')
async def login(request:Request):
    """Page the discord login redirects the user to when successfully logged in with Discord"""

    await webutils.process_discord_login(request, ['identify', 'guilds'])
    return HTTPFound(location=f'/settings')
