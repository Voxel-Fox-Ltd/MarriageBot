from aiohttp.web import RouteTableDef, Request, Response
import bootstrap_builder as bb

from website import utils as webutils


routes = RouteTableDef()


@routes.get("/")
async def index(request:Request):
    """Index of the website"""

    page = bb.HTMLPage()
    with page.new_container().new_row() as row:
        row.new_column().new_child("p", "Woah what the fuck")
        row.new_column().new_child("p", "Haha nice")
        row.new_column().new_child("a", "Test", href=webutils.get_discord_login_url(request, "http://localhost:8080/login"))

    # Wew whatever
    return Response(text=page.to_string(), content_type="text/html")