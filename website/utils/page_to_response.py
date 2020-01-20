import functools

from aiohttp.web import Response
import bootstrap_builder as bb


def page_to_response():
    def wrapper(func):
        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            data = await func(*args, **kwargs)
            if isinstance(data, bb.HTMLNode):
                return Response(text=data.to_string(), content_type="text/html")
            return data
        return wrapped
    return wrapper
