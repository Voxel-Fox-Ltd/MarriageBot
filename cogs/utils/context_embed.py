import random

import discord


class ContextEmbed(discord.Embed):
    """A small mod for discord.Embed that allows for some of the more common things
    that I tend to do with them"""

    def __init__(self, *args, use_random_colour:bool=False, **kwargs):
        super().__init__(*args, **kwargs)
        if use_random_colour:
            self.use_random_colour()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def use_random_colour(self):
        """Sets the colour for the embed to a random one"""

        self.colour = random.randint(0, 0xffffff)
        return self

    def set_footer(self, text:str, *args, **kwargs):
        """Sets the footer of the embed"""

        super().set_footer(*args, text=text, **kwargs)
        return self

    def set_image(self, url:str):
        """Sets the image of the embed"""

        super().set_image(url=url)
        return self

    def set_thumbnail(self, url:str):
        """Sets the thumbnail of the embed"""

        super().set_image(url=url)
        return self

    def set_author_to_user(self, user:discord.User):
        """Sets the author of the embed to a given Discord user"""

        super().set_author(name=str(user), icon_url=user.avatar_url)
        return self

    def add_field(self, name:str, value:str, inline:bool=True):
        """Adds a field to the embed without using kwargs"""

        super().add_field(name=name, value=value, inline=inline)
        return self

    def edit_field_by_index(self, index:int, *, name:str=None, value:str=None, inline:bool=None):
        """Edit a field in the embed using its index"""

        field = self.fields[index]
        new_name = name or field.name
        new_value = value or field.value
        new_inline = inline if inline is not None else field.inline
        super().set_field_at(index, name=new_name, value=new_value, inline=new_inline)
        return self

    def edit_field_by_key(self, key:str, *, name:str=None, value:str=None, inline:bool=None):
        """Edit a field in the embed using its name as a key"""

        for index, field in enumerate(self.fields):
            if field.name == key:
                return self.edit_field_by_index(index, name=name, value=value, inline=inline)
        raise KeyError("Key not found in embed")
