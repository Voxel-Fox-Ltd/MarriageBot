from argparse import ArgumentParser
from ssl import SSLContext
from os import getcwd

from aiohttp.web import Application, run_app
from aiohttp_jinja2 import setup as jinja_setup
from aiohttp_session import setup as session_setup, SimpleCookieStorage
from aiohttp_session.cookie_storage import EncryptedCookieStorage as ECS
from jinja2 import FileSystemLoader

# from website.api import routes as api_routes
from website.frontend2 import routes as frontend_routes


# Parse arguments
parser = ArgumentParser()
parser.add_argument("--host", type=str, default='0.0.0.0',  help="The host IP to run the webserver on.")
parser.add_argument("--port", type=int, default=8080,  help="The port to run the webserver on.")
args = parser.parse_args()


# Create website
app = Application(debug=True)
# app.add_routes(api_routes)
app.add_routes(frontend_routes)
app.router.add_static('/static', getcwd() + '/website/static')
app['static_root_url'] = '/static'
jinja_setup(app, loader=FileSystemLoader(getcwd() + '/website/templates'))
# session_setup(app, ECS(token_bytes(32)))
session_setup(app, SimpleCookieStorage())


if __name__ == '__main__':
    run_app(app, host=args.host, port=args.port)
