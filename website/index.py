from aiohttp.web import Response, RouteTableDef

routes = RouteTableDef()


@routes.get('/')
async def secret(request):
    return Response(text=str(len(request.app['bot'].guilds)))
