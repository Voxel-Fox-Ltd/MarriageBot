import json
from datetime import datetime as dt

import aiohttp_session
from aiohttp.web import HTTPFound, Request, RouteTableDef, Response

from website import utils as webutils

routes = RouteTableDef()


@routes.get('/login_redirect')
async def login(request:Request):
    """Page the discord login redirects the user to when successfully logged in with Discord"""

    await webutils.process_discord_login(request, ['identify', 'guilds'])
    session = await aiohttp_session.get_session(request)
    return HTTPFound(location=session.pop('redirect_on_login', '/'))


@routes.post('/webhooks/voxel_fox/paypal_purchase')
async def paypal_purchase_complete(request:Request):
    """Handles Paypal throwing data my way"""

    # Check the headers
    if request.headers.get("Authorization", None) != request.app['config']['authorization_tokens']['paypal']:
        return Response(status=200)
    data = await request.json()
    custom_data = json.loads(data['custom'])

    async with request.app['database']() as db:
        if data['refunded'] is False:
            pass
        else:
            pass

    # Let the user get redirected
    return Response(status=200)


@routes.post('/webhooks/voxel_fox/topgg')
async def webhook_handler(request:Request):
    """Sends a PM to the user with the webhook attached if user in owners"""

    if request.headers.get('Authorization', None) != request.app['config']['topgg_authorization']:
        return Response(400)
    data = await request.json()
    time = dt.utcnow()

    # Send proper thanks to the user
    text = {
        'upvote': 'Thank you for upvoting!',
        'test': 'Thanks for the test ping boss.',
    }.get(data['type'], 'Invalid webhook type from DBL')

    # Redis thanks to user
    async with request.app['redis']() as re:
        await re.publish_json("SendUserMessage", {"user_id": data['user_id'], "content": text})
        await re.publish_json('DBLVote', {'user_id': data['user_id'], 'datetime': time.isoformat()})

    # DB vote
    async with request.app['database']() as db:
        await db('INSERT INTO dbl_votes (user_id, timestamp) VALUES ($1, $2) ON CONFLICT (user_id) DO UPDATE SET timestamp=excluded.timestamp', data['user_id'], time)
    return Response(status=200)
