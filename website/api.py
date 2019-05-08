from json import dumps
from datetime import datetime as dt

from aiohttp.web import Response, RouteTableDef, Request

from cogs.utils.custom_bot import CustomBot
from cogs.utils.customised_tree_user import CustomisedTreeUser


routes = RouteTableDef()


@routes.post('/webhook/dbl')
async def webhook_handler(request:Request):
    '''
    Sends a PM to the user with the webhook attached if user in owners
    '''
    
    # Set up some stuff
    bot = request.app['bot']
    success = Response(
        text=dumps({"success": True}),
        content_type="application/json"
    )
    failure = lambda x: Response(
        text=dumps({"success": False, **x}),
        content_type="application/json"
    )
    try:
        x = await request.json()
    except Exception:
        return failure({'reason': 'No JSON response'})

    # See if it's all valid
    if 'bot' in x and 'user' in x and 'type' in x:
        pass 
    else:
        return failure({'reason': 'Invalid request params'}) # No valid points
    try:
        if int(x['bot']) not in [bot.user.id, 488227732057227265]:
            return failure({'reason': 'Invalid bot ID'})
    except ValueError:
        # Bot ID wasn't an integer
        return failure({'reason': 'Invalid bot ID'})
    try:
        user = await bot.fetch_user(int(x['user']))
        user_id = int(x['user'])
    except ValueError:
        # User ID wasn't an integer
        return failure({'reason': 'Invalid user ID'})
    if x['type'] not in ['upvote', 'test']:
        return failure({'reason': 'Invalid request type'})

    # Send proper thanks to the user
    try:
        if x['type'] == 'upvote':
            await user.send("Thank you for upvoting MarriageBot!")
        elif x['type'] == 'test':
            await user.send("Thanks for the text ping boss.")
    except Exception:
        # Couldn't send them a message oops
        pass 

    # Database it up
    # bot.dbl_votes[user_id] = dt.now()
    async with bot.redis() as re:
        await re.publish_json('DBLVote', {'user_id': user.id, 'datetime': dt.now().isoformat()})
    async with bot.database() as db:
        try:
            await db('INSERT INTO dbl_votes (user_id, timestamp) VALUES ($1, $2)', user_id, bot.dbl_votes[user_id])
        except Exception as e:
            await db('UPDATE dbl_votes SET timestamp=$2 WHERE user_id=$1', user_id, bot.dbl_votes[user_id])
    return success
