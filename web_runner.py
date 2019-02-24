from argparse import ArgumentParser
from secrets import token_bytes
from ssl import SSLContext
from os.path import join as join_path, dirname

from aiohttp.web import Application, AppRunner, TCPSite, run_app, Response, get, static
from aiohttp_jinja2 import template, setup as jinja_setup
from aiohttp_session import setup as session_setup
from aiohttp_session.cookie_storage import EncryptedCookieStorage as ECS
from jinja2 import FileSystemLoader

from website.api import routes as api_routes
from website.frontend import routes as frontend_routes



# Parse arguments
parser = ArgumentParser()
parser.add_argument(
    "-i", "--host", 
    type=str,
    default='0.0.0.0', 
    help="The host IP to run the webserver on."
)
parser.add_argument(
    "-p", "--port", 
    type=int,
    default=8080, 
    help="The port to run the webserver on."
)
args = parser.parse_args()


# Create website
app = Application(debug=True)
# app.add_routes(api_routes)
app.add_routes(frontend_routes)
app['static_root_url'] = '/static'


async def handle_test(request):
    return Response(text='Test')


app.add_routes([
    get('/test', handle_test),
    static('/static', '/root/MarriageBot/website/static'),
])


# Set up aiohttp extensions
jinja_setup(app, loader=FileSystemLoader('website/templates'))
session_setup(app, ECS(token_bytes(32)))


if __name__ == '__main__':
    run_app(app, host=args.host, port=args.port)
