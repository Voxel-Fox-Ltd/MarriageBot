def get_avatar(user_info:dict=dict()):
    """Gets the avatar URL for a user when provided with their user info
    If no arguments are provided then the default Discord avatar is given"""

    try:
        return f"https://cdn.discordapp.com/avatars/{user_info['id']}/{user_info['avatar']}.png"
    except KeyError:
        try:
            return f"https://cdn.discordapp.com/embed/avatars/{int(user_info['discriminator']) % 5}.png"
        except KeyError:
            pass
    return "https://cdn.discordapp.com/embed/avatars/0.png"
