from aiohttp.web import Request


def get_bot():
    def outer(func):
        def wrapper(request:Request, *args, **kwargs):
            bot = request.app['bot']
            func(bot, request, *args, **kwargs)
        return wrapper
    return outer
