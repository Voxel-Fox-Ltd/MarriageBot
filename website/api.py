from datetime import datetime as dt

from aiohttp.web import Response, RouteTableDef, Request
import json
import discord
import asyncpg


routes = RouteTableDef()


@routes.post('/webhook/dbl')
async def webhook_handler(request:Request):
    """Sends a PM to the user with the webhook attached if user in owners"""

    # Get our data
    bot = request.app['bot']

    # Set up our responses
    success = Response(text=json.dumps({"success": True}), content_type="application/json")
    failure = lambda x: Response(text=json.dumps({"success": False, **x}), content_type="application/json")

    # See if we can get it
    try:
        x = await request.json()
    except Exception:
        return failure({'reason': 'No JSON response'})

    # See if it's all valid
    keys = set(['bot', 'user', 'type'])
    if set(x.keys()) != keys:
        return failure({'reason': 'Invalid request params'})

    # Check the bot's ID
    try:
        if int(x['bot']) != bot.user.id:
            return failure({'reason': 'Invalid bot ID'})  # wrong bot
    except ValueError:
        return failure({'reason': 'Invalid bot ID'})  # not an int

    # Check user's ID
    try:
        user_id = int(x['user'])
        user = await bot.fetch_user(user_id)
    except ValueError:
        return failure({'reason': 'Invalid user ID'})  # uid wasn't int
    except (discord.Forbidden, discord.NotFound):
        user = None

    # Check type
    if x['type'] not in ['upvote', 'test']:
        return failure({'reason': 'Invalid request type'})

    # Send proper thanks to the user
    try:
        if x['type'] == 'upvote':
            await user.send("Thank you for upvoting MarriageBot!")
        elif x['type'] == 'test':
            await user.send("Thanks for the text ping boss.")
    except (discord.Forbidden, discord.NotFound, AttributeError):
        pass  # couldn't send or not found user

    # Database it up
    time = dt.now()
    async with bot.redis() as re:
        await re.publish_json('DBLVote', {'user_id': user.id, 'datetime': time.isoformat()})
    async with bot.database() as db:
        try:
            await db('INSERT INTO dbl_votes (user_id, timestamp) VALUES ($1, $2)', user_id, time)
        except asyncpg.UniqueViolationError:
            await db('UPDATE dbl_votes SET timestamp=$2 WHERE user_id=$1', user_id, time)
    return success
