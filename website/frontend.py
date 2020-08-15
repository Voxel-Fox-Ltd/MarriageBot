import copy

import aiohttp_session
import discord
from aiohttp.web import HTTPFound, Request, RouteTableDef, json_response
from aiohttp_jinja2 import template
import markdown2

from cogs import utils
from website import utils as webutils


routes = RouteTableDef()


@routes.get("/")
@template('index.j2')
@webutils.add_output_args()
async def index(request:Request):
    """Index of the website, has "login with Discord" button
    If not logged in, all pages should redirect here"""

    return {}


@routes.get("/blog/{code}")
@template('blog.j2')
@webutils.add_output_args()
async def blog(request:Request):
    """Blog post handler"""

    # Grab the blog post from database
    url_code = request.match_info['code']
    async with request.app['database']() as db:
        data = await db("SELECT * FROM blog_posts WHERE url=$1", url_code)
    if not data:
        return {'title': 'Post not found'}

    # Return the article and the opengraph stuff
    text = data[0]['body']
    return {
        'text': markdown2.markdown(text),
        'title': data[0]['title'],
        'opengraph': {
            'article:published_time': data[0]['created_at'].isoformat(),
            'article:modified_time': data[0]['created_at'].isoformat(),
            'og:type': 'article',
            'og:title': f"MarriageBot - {data[0]['title']}",
            'og:description': text.split('\n')[0],
        }
    }


@routes.get('/settings')
@template('settings.j2')
@webutils.add_output_args()
@webutils.requires_login()
async def settings(request:Request):
    """Handles the main settings page for the bot"""

    return {}


@routes.get('/user_settings')
@template('user_settings.j2')
@webutils.add_output_args()
@webutils.requires_login()
async def user_settings(request:Request):
    """Handles the users' individual settings pages"""

    # See if they're logged in
    session = await aiohttp_session.get_session(request)

    # Get the colours they're using
    db = await request.app['database'].get_connection()
    if len(request.query) > 0:
        colours_raw = {
            'edge': request.query.get('edge'),
            'node': request.query.get('node'),
            'font': request.query.get('font'),
            'highlighted_font': request.query.get('highlighted_font'),
            'highlighted_node': request.query.get('highlighted_node'),
            'background': request.query.get('background'),
            'direction': request.query.get('direction', 'TB'),
        }
        colours = {}
        for i, o in colours_raw.items():
            if o is None:
                o = 'transparent'
            colours[i] = o
    else:
        data = await db('SELECT * FROM customisation WHERE user_id=$1', session['user_id'])
        try:
            colours = utils.CustomisedTreeUser(**data[0]).unquoted_hex
        except (IndexError, TypeError):
            colours = utils.CustomisedTreeUser.get_default_unquoted_hex()

    # Make a URL for the preview
    tree_preview_url = '/tree_preview?' + '&'.join([f'{i}={o.strip("#")}' if i != 'direction' else f'{i}={o}' for i, o in colours.items()])

    # Get their blocked users
    blocked_users_db = await db("SELECT blocked_user_id FROM blocked_user WHERE user_id=$1", session['user_id'])
    blocked_users = {i['blocked_user_id']: await request.app['bot'].get_name(i['blocked_user_id']) for i in blocked_users_db}

    # Give all the data to the page
    await db.disconnect()
    return {
        'hex_strings': colours,
        'tree_preview_url': tree_preview_url,
        'blocked_users': blocked_users,
    }


@routes.get("/logout")
async def logout(request:Request):
    """Index of the website"""

    session = await aiohttp_session.get_session(request)
    session.invalidate()
    return HTTPFound(location='/')


@routes.get("/guilds")
@template('guild_picker.j2')
@webutils.add_output_args()
@webutils.requires_login()
async def guild_picker(request:Request):
    """Shows the guilds that the user has permission to change"""

    # Get the guilds they're valid to alter
    all_guilds = await webutils.get_user_guilds(request)
    if all_guilds is None:
        return HTTPFound(location='/discord_oauth_login')
    try:
        guilds = [i for i in all_guilds if i['owner'] or i['permissions'] & 40 > 0]
    except TypeError:
        # No guilds provided - did they remove the scope? who knows
        guilds = []
    guild_ids = [int(i['id']) for i in guilds]

    # Add a gold attribute to the guilds
    async with request.app['database']() as db:
        gold_guild_data = await db("SELECT * FROM guild_specific_families WHERE guild_id=ANY($1::BIGINT[])", guild_ids)
    gold_guild_ids = [str(i['guild_id']) for i in gold_guild_data]
    for i in guilds:
        if i['id'] in gold_guild_ids:
            i['gold'] = True
        else:
            i['gold'] = False

    # See if they bought any of the gold instances
    session = await aiohttp_session.get_session(request)
    user_id = session['user_id']
    request.app['logger'].info("Getting user data")
    rows = [i for i in gold_guild_data if i['purchased_by'] == user_id]
    if rows:
        await webutils.add_user_to_guild(request, request.app['config']['guild_id'])
        async with request.app['redis']() as re:
            await re.publish_json("AddGoldUser", {'user_id': user_id})

    # Send off guilds to the page
    return {'guilds': guilds}


@routes.get('/tree_preview')
@template('tree_preview.j2')
@webutils.add_output_args()
async def tree_preview(request:Request):
    """Tree preview for the bot"""

    # Grab the colours from the params
    colours_raw = {
        'edge': request.query.get('edge'),
        'node': request.query.get('node'),
        'font': request.query.get('font'),
        'highlighted_font': request.query.get('highlighted_font'),
        'highlighted_node': request.query.get('highlighted_node'),
        'background': request.query.get('background'),
        'direction': request.query.get('direction'),
    }

    # Fix it up to be usable values
    colours = {}
    for i, o in colours_raw.items():
        if o is None or o == 'transparent':
            o = 'transparent'
        elif i == 'direction':
            pass
        else:
            o = f'#{o.strip("#")}'
        colours[i] = o

    # Return it to the page
    return {
        'hex_strings': colours,
    }


@routes.get('/guild_settings')
@template('guild_settings_paypal.j2')
@webutils.add_output_args()
@webutils.requires_login()
async def guild_settings_get_paypal(request:Request):
    """Shows the settings for a particular guild"""

    # See if they're logged in
    guild_id = request.query.get('guild_id')
    gold_param = request.query.get('gold', '0') == '1'
    if not guild_id:
        return HTTPFound(location='/')

    # Get the bot object
    if gold_param:
        bot = request.app['gold_bot']
    else:
        bot = request.app['bot']

    # See if the bot is in the guild
    try:
        guild_object = await bot.fetch_guild(int(guild_id))
    except discord.Forbidden:
        # We get here? Bot's not in the server
        location = bot.get_invite_link(
            redirect_uri='https://marriagebot.xyz/guild_settings',
            response_type='code',
            scope='bot identify guilds guilds.join',
            read_messages=True,
            send_messages=True,
            attach_files=True,
            embed_links=True,
            guild_id=guild_id,
        )
        return HTTPFound(location=location)

    # Get the guilds they're able to alter
    all_guilds = await webutils.get_user_guilds(request)
    if all_guilds is None:
        return HTTPFound(location='/discord_oauth_login')
    oauth_guild_data = [i for i in all_guilds if (i['owner'] or i['permissions'] & 40 > 0) and guild_id == i['id']]
    if not oauth_guild_data:
        return HTTPFound(location='/')

    # Get the current guild data from the database
    async with request.app['database']() as db:

        # Get guild settings
        guild_settings = await db('SELECT * FROM guild_settings WHERE guild_id=$1', int(guild_id)) or [request.app['bot'].DEFAULT_GUILD_SETTINGS.copy()]

        # Get gold allowance
        if not gold_param:
            gold_settings = await db('SELECT * FROM guild_specific_families WHERE guild_id=$1', int(guild_id))

        # Get disabled commands
        disabled_commands = {i: False for i in request.app['config']['disableable_commands']}
        disable_data = await db('SELECT * FROM disabled_commands WHERE guild_id=$1', int(guild_id))
        for row in disable_data:
            disabled_commands[row['command_name']] = row['disabled']

        # Get children amount
        max_children_data = await db('SELECT * FROM max_children_amount WHERE guild_id=$1', int(guild_id))
        max_children_amount = {i['role_id']: i['amount'] for i in max_children_data}

    # Get prefix
    try:
        prefix = guild_settings[0]['gold_prefix' if gold_param else 'prefix']
    except (IndexError, KeyError):
        prefix = request.app['gold_config' if gold_param else 'config']['prefix']['default_prefix']

    # Get channel objects from the guild
    channels = sorted([i for i in await guild_object.fetch_channels() if isinstance(i, discord.TextChannel)], key=lambda c: c.position)
    roles = sorted([i for i in await guild_object.fetch_roles()], key=lambda c: c.position, reverse=True)

    # Get the normal bot data
    if gold_param:
        non_gold_bot = request.app['bot']
        try:
            guild_object = await non_gold_bot.fetch_guild(int(guild_id))
            normal_bot_data = True
        except discord.Forbidden:
            normal_bot_data = False
    else:
        normal_bot_data = None

    # Get the gold bot data
    if gold_param:
        gold_bot_data = None
    else:
        gold_bot_data = bool(gold_settings)

    # Return info to the page
    page_data = {
        'guild': guild_object,  # The guild object as we know it
        'prefix': prefix,  # The prefix for the bot
        'channels': channels,  # The channel objects for the guild
        'gold': gold_bot_data,  # Whether the guild has gold or not - 'None' for showing the gold page
        'normal': normal_bot_data,  # Whether the guild has the normal bot or not - 'None' for showing the normal page
        'max_family_members': guild_settings[0]['max_family_members'],  # Maximum amount of family members
        'allow_incest': guild_settings[0]['allow_incest'],  # Whether incest is allowed or not
        'disabled_commands': disabled_commands,  # The commands that are disabled
        'roles': roles,  # The role objects for the guild
        'max_children_amount': max_children_amount,  # Children amounts for this guild
        'gifs_enabled': guild_settings[0]['gifs_enabled'],  # Children amounts for this guild
        'max_children_hard_cap': max([i['max_children'] for i in request.app['config']['role_perks'].values()]),  # Hard cap on children for all users
        'min_children_hard_cap': min([i['max_children'] for i in request.app['config']['role_perks'].values()]),  # Hard minimum on children for all users
    }
    return page_data


@routes.get("/discord_oauth_login")
async def login(request:Request):
    """The redirect to the actual oauth login"""

    bot = request.app['bot']
    login_url = bot.get_invite_link(
        redirect_uri='https://marriagebot.xyz/login_redirect',
        response_type='code',
        scope='identify guilds guilds.join',
        read_messages=True,
        send_messages=True,
        attach_files=True,
        embed_links=True,
    )
    return HTTPFound(location=login_url)
