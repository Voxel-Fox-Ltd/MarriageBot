from json import dumps
from aiohttp.web import Response, RouteTableDef, Request
from cogs.utils.custom_bot import CustomBot
from website.utils.decorators import get_bot

routes = RouteTableDef()


@routes.get('/')
@get_bot()
async def secret(bot:CustomBot, request:Request):
    return Response(text=str(len(bot.guilds)))


@routes.post('/webhook')
@get_bot()
async def webhook_handler(bot:CustomBot, request:Request):
    '''
    Sends a PM to the user with the webhook attached if user in owners
    '''

    x = await request.json()
    print(dumps(x))
    if x['bot'] != bot.user.id:
        return
    if x['user'] in bot.owners:
        owner = bot.get_user(x['user'])
        await owner.send(dumps(x))
    return Response(text='')


@routes.get('/webhook')
@get_bot()
async def webhook_handler2(bot:CustomBot, request:Request):
    '''
    Sends a PM to the user with the webhook attached if user in owners
    '''

    x = await request.json()
    print(dumps(x))
    return Response(text=dumps(x))
    if x['bot'] != bot.user.id:
        return
    if x['user'] in bot.owners:
        owner = bot.get_user(x['user'])
        await owner.send(dumps(x))
    return Response(text='')

