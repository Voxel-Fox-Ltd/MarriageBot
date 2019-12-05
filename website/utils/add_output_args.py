from aiohttp.web import Request, HTTPFound


def add_output_args(*, redirect_if_logged_out:str=None, redirect_if_logged_in:str=None):
    """This function is a wrapper around all routes. It takes the output and
    adds the user info and request to the returning dictionary
    It must be applied before the template decorator"""

    def inner_wrapper(func):
        """An inner wrapper so I can get args at the outer level"""

        async def wrapper(request:Request):
            """This is the wrapper that does all the heavy lifting"""

            # Run function
            data = await func(request)

            # See if we return anything other than data (like redirects)
            if not isinstance(data, dict):
                return data

            # Update data with the information
            if data is None:
                data = dict()
            session = await aiohttp_session.get_session(request)
            try:
                data.update({'user_info': session['user_info']})
            except KeyError:
                data.update({'user_info': None})
            data.update({'request': request})

            # Check return relevant info
            if redirect_if_logged_out and session.get('user_id') is None:
                return HTTPFound(location=redirect_if_logged_out)
            elif redirect_if_logged_in and session.get('user_id') is not None:
                return HTTPFound(location=redirect_if_logged_in)

            return data
        return wrapper
    return inner_wrapper
