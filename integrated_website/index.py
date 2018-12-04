from json import dumps

from aiohttp.web import Response, RouteTableDef, Request

from cogs.utils.custom_bot import CustomBot
from cogs.utils.customised_tree_user import CustomisedTreeUser


routes = RouteTableDef()


@routes.get('/user')
async def user_handler(request:Request):
    '''
    Handles the user GET request to either get user data
    '''

    parameters = request.rel_url.query
    user_data = CustomisedTreeUser.get(int(parameters['user_id']))
    return Response(
        content_type="application/json",
        text=dumps({i:o.strip('"#') for i, o in user_data.hex.items()})
    )


@routes.post('/user')
async def user_post_handler(request:Request):
    '''
    Handles the user POST request to save user data to the database
    '''

    bot = request.app['bot']
    data = await request.json()
    async with bot.database() as db:
        try:
            await db(
                "INSERT INTO customisation (user_id, edge, node, font, highlighted_font, highlighted_node, background) VALUES ($1, $2, $3, $4, $5, $6, $7)",
                int(data['user_id']),
                int(data['edge'], 16),
                int(data['node'], 16),
                int(data['font'], 16),
                int(data['highlighted_font'], 16),
                int(data['highlighted_node'], 16),
                int(data['background', 16]),
            )
        except Exception: 
            await db(
                "UPDATE customisation SET edge=$2, node=$3, font=$4, highlighted_font=$5, highlighted_node=$6, background=$7 WHERE user_id=$1",
                int(data['user_id']),
                int(data['edge'], 16),
                int(data['node'], 16),
                int(data['font'], 16),
                int(data['highlighted_font'], 16),
                int(data['highlighted_node'], 16),
                int(data['background'], 16),
            )
    int_values = {i:int(o, 16) for i, o in data.items() if i != 'user_id'}
    CustomisedTreeUser(int(data['user_id']), **int_values)
    return Response(
        text=dumps({"success": True}),
        content_type="application/json"
    )


@routes.get('/guild')
async def guild_handler(request:Request):
    '''
    Handles the user GET request to either get guild prefix data
    '''

    bot = request.app['bot']
    parameters = request.rel_url.query
    guild_id = int(parameters['guild_id'])
    try:
        guild_prefix = bot.guild_prefixes.get(guild_id, bot.config['default_prefix'])
    except AttributeError:
        guild_prefix = bot.config['default_prefix']
    return Response(
        content_type="application/json",
        text=dumps({"guild_prefix": guild_prefix})
    )



@routes.post('/guild')
async def guild_post_handler(request:Request):
    '''
    Handles the user GET request to either get guild prefix data
    '''

    bot = request.app['bot']
    data = await request.json()
    guild_id = int(data['guild_id'])
    user_id = data['user_id']
    guild = bot.get_guild(guild_id)
    member = guild.get_member(user_id)
    if member.guild_permissions.administrator or member.guild_permissions.manage_guild or guild.owner.id == member.id:
        pass
    else:
        return Response(
            text=dumps({"success": False}),
            content_type="application/json"
        )
    async with bot.database() as db:
        try:
            await db("INSERT INTO guild_settings (guild_id, prefix) VALUES ($1, $2)", guild_id, data['prefix'])
        except Exception:
            await db("UPDATE guild_settings SET prefix=$1 WHERE guild_id=$2", data['prefix'], guild_id)
    bot.guild_prefixes[guild_id] = data['prefix']
    return Response(
        text=dumps({"success": True}),
        content_type="application/json"
    )


@routes.post('/webhook')
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
    failure = Response(
        text=dumps({"success": False}),
        content_type="application/json"
    )
    x = await request.json()

    # See if it's all valid
    if 'bot' in x and 'user' in x and 'type' in x:
        pass 
    else:
        return failure  # No valid points
    try:
        if int(x['bot']) != bot.user.id:
            return failure
    except ValueError:
        # Bot ID wasn't an integer
        return failure
    try:
        user = bot.get_user(int(x['user']))
    except ValueError:
        # User ID wasn't an integer
        return failure
    if x['type'] not in ['upvote', 'test']:
        return failure

    # Send proper thanks to the user
    await user.send("Thank you for upvoting MarriageBot!")
    return Response(
        text=dumps({"success": True}),
        content_type="application/json"
    )
