from os import getcwd
from json import dumps

from aiohttp import ClientSession
from aiohttp.web import RouteTableDef, Request, HTTPFound, static, Response
from aiohttp_session import new_session, get_session
from aiohttp_jinja2 import template

from cogs.utils.customised_tree_user import CustomisedTreeUser


routes = RouteTableDef()


@routes.get("/")
@routes.get("/home")
@routes.get("/index")
@template('index.jinja')
async def index(request:Request):
    '''
    Index of the website
    Has "login with Discord" button
    If not logged in, all pages should redirect here
    '''

    session = await get_session(request)
    if not session.get('user_info'):
        return {}
    user_info = session.get('user_info')
    return HTTPFound(location=f'/colours/{user_info["id"]}')


@routes.get('/login')
@routes.post('/login')
async def login(request:Request):
    '''
    Page the discord login redirects the user to when successfully logged in with Discord
    '''

    # Get the code
    code = request.query.get('code')
    if not code:
        return HTTPFound(location='/')

    # Get the bot
    bot = request.app['bot']
    oauth_data = bot.config['oauth']

    # Generate the post data
    data = {
        'grant_type': 'authorization_code',
        'code': code, 
        'scope': 'identify guilds',
    }
    data.update(oauth_data)
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    # Make the request
    async with ClientSession(loop=request.loop) as session:
        token_url = f"https://discordapp.com/api/v6/oauth2/token"
        async with session.post(token_url, data=data, headers=headers) as r:
            token_info = await r.json()
        headers.update({
            "Authorization": f"{token_info['token_type']} {token_info['access_token']}"
        })
        user_url = f"https://discordapp.com/api/v6/users/@me"
        async with session.get(user_url, headers=headers) as r:
            user_info = await r.json()
        guilds_url = f"https://discordapp.com/api/v6/users/@me/guilds"
        async with session.get(guilds_url, headers=headers) as r:
            guild_info = await r.json()

    # Process it all up
    session = await new_session(request)
    session['user_info'] = user_info
    session['guild_info'] = guild_info
    # return Response(
    #     text=dumps(dict(session)),
    #     content_type='application/json'
    # )
    return HTTPFound(location=f'/colours/{user_info["id"]}')


@routes.get('/colours/{user_id}')
@template('colours.jinja')
async def colours(request:Request):
    '''
    Handles the colours page for the user
    '''

    # Check they're logged in
    session = await get_session(request)
    if not session.get('user_info'):
        return HTTPFound(location='/')

    # Check they're giving a user ID in the URL
    user_id = request.match_info.get('user_id')
    if not user_id:
        return HTTPFound(location=f'/colours/{session["user_info"]["id"]}')

    # Get their current values and punch em out to the user
    ctu = CustomisedTreeUser.get(int(user_id))
    return {
        'user': session.get('user_info'), 
        'hex_strings': ctu.unquoted_hex,
    }


@routes.get('/logout')
async def logout(request:Request):
    '''
    Logs out the user and destroys their session
    '''

    session = await get_session(request)
    session.invalidate()
    return HTTPFound(location='/')


# @app.route("/submit_colours", methods=['post','get'])
# def submit_colours():
#     colours = request.form
#     user_object = users.get(session.get("user_token"))

#     Marriagebot.set_colours(
#         user_id=user_object.id,
#         edge=colours["edge_colour"].strip('#'),
#         node=colours["node_colour"].strip('#'),
#         font=colours["font_colour"].strip('#'),
#         highlighted_font=colours["highlighted_font_colour"].strip('#'),
#         highlighted_node=colours["highlighted_node_colour"].strip('#'),
#         background=colours["background_colour"].strip('#')
#     )
#     return redirect("/colours")

# @app.route("/submit_prefix/<guild_id>",methods=['post'])
# def submit_prefix(guild_id):
#     prefix=request.form.get("prefix")
#     user_object=users.get(session.get("user_token"))
#     guild_object=user_object.get_guild(guild_id)
#     guild_object.prefix=prefix
#     Marriagebot.set_prefix(
#         guild_id=guild_object.id,
#         prefix=prefix,
#         user_id=user_object.id
#     )
#     return redirect("/guilds/"+guild_id)   


# @app.route("/colours",methods=["post","get"])
# def colours():
#     '''
#     Page that allows user to select colours and submit them
#     '''

#     if session.get("user_token") is None:
#         return redirect("/")
        
#     user_object = users.get(session.get("user_token"))
#     colours = Marriagebot.get_colours(user_object.id)
#     guild_list = user_object.guild_list
#     return render_template(
#         "colours.html",
#         colours_url="/colours",
#         guilds_url="/guilds",
#         logout_url="/logout",
#         user_avatar=user_object.get_avatar_url(),
#         username=user_object.get_name(),
#         marriagebot_logo="http://hatton-garden.net/blog/wp-content/uploads/2012/03/wedding-rings.jpg",
#         edge_colour=colours["edge"],
#         node_colour=colours["node"],
#         font_colour=colours["font"],
#         highlighted_font_colour=colours["highlighted_font"],
#         highlighted_node_colour=colours["highlighted_node"],
#         background_colour=colours["background"],
#         guild_list=guild_list
#     )


# @app.route("/guilds", methods=["post","get"])
# def guilds():
#     '''
#     Page that allows user to select guild out of guilds they own
#     '''

#     if session.get("user_token") is None:
#         return redirect("/")

#     user_object = users.get(session.get("user_token"))
#     guilds = user_object.guild_list
#     return redirect(f"/guilds/{guilds[0].id}")


# @app.route("/guilds/<guild_id>", methods=["get"])
# def selected_guild(guild_id):
#     if session.get("user_token") is None:
#         return redirect("/")

#     user_object=users.get(session.get("user_token"))
#     guild_list=user_object.guild_list
#     selected_guild=user_object.get_guild(guild_id)

#     return render_template(
#         "guilds.html",
#         colours_url="/colours",
#         guilds_url="/guilds",
#         logout_url="/logout",
#         user_avatar=user_object.get_avatar_url(),
#         username=user_object.get_name(),
#         marriagebot_logo="http://hatton-garden.net/blog/wp-content/uploads/2012/03/wedding-rings.jpg",
#         guild_list=guild_list,
#         selected_guild=selected_guild
#     )
