from aiohttp.web import RouteTableDef, Request, HTTPFound

from website import utils as webutils


routes = RouteTableDef()


@routes.get('/login')
async def login(request:Request):
    """Page the discord login redirects the user to when successfully logged in with Discord"""

    await webutils.process_discord_login(request)
    return HTTPFound(location=f'/settings')
