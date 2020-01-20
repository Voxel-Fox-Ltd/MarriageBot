from aiohttp.web import RouteTableDef, Request, Response, HTTPFound

from website import utils as webutils


routes = RouteTableDef()


@routes.get("/")
@webutils.page_to_response()
async def index(request:Request):
    """Index of the website"""

    page = webutils.bb.HTMLPage.load_from_default('main')
    container = page.shortcuts['container']
    container.new_row().new_column().new_child("p", "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam tellus metus, porttitor sit amet odio in, pellentesque fermentum nisi. Orci varius natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Quisque sit amet blandit justo. Mauris non tortor mattis nulla efficitur sodales ut sit amet sem. Quisque id eleifend felis. Cras eleifend dolor eros, quis feugiat elit pharetra id. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae; Fusce purus diam, ultrices in suscipit nec, congue ut turpis. Sed tincidunt feugiat eros vel congue. Quisque feugiat dolor quam, placerat eleifend ante placerat sed. Nam non nisl lectus.")
    container.new_row().new_column().new_child("p", "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam tellus metus, porttitor sit amet odio in, pellentesque fermentum nisi. Orci varius natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Quisque sit amet blandit justo. Mauris non tortor mattis nulla efficitur sodales ut sit amet sem. Quisque id eleifend felis. Cras eleifend dolor eros, quis feugiat elit pharetra id. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae; Fusce purus diam, ultrices in suscipit nec, congue ut turpis. Sed tincidunt feugiat eros vel congue. Quisque feugiat dolor quam, placerat eleifend ante placerat sed. Nam non nisl lectus.")
    return page


@routes.get("/discord_oauth_login")
async def login(request:Request):
    """Index of the website"""

    login_url = webutils.get_discord_login_url(
        request,
        redirect_uri="http://localhost:8080/login_redirect",
        oauth_scopes=['identify', 'guilds'],
    )
    return HTTPFound(location=login_url)
