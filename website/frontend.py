from aiohttp.web import RouteTableDef, Request
from aiohttp_jinja2 import template

from website import utils as webutils
import htmlbuilder


"""
All pages on this website that implement the base.jinja file should return two things:
Firstly, the original request itself under the name 'request'.
Secondly, it should return the user info from the user as gotten from the login under 'user_info'
This is all handled by a decorator below - webutils.add_output_args - but I'm just putting it here as a note
"""


routes = RouteTableDef()


@routes.get("/")
@template('bs.jinja')
@webutils.add_output_args()
async def index(request:Request):
    """Index of the website"""

    with htmlbuilder.Page() as page:
        with page.new_container() as container:
            with container.new_row() as row:
                row.new_column(text=htmlbuilder.Node("p", "Woah what the fuck"))
                row.new_column(text=htmlbuilder.Node("p", "Haha nice"))

    # Wew whatever
    return {
        'page': page.to_json()
    }