import re as regex
import random

import discord
from discord.ext import commands


class CustomContext(commands.Context):
    """A custom subclass of commands.Context that embeds all content"""

    DEFAULT_FOOTER_TEXT = [{'text': 'MarriageBot'}]
    DESIRED_PERMISSIONS = discord.Permissions(18432)  # embed links, send messages
    USER_ID_REGEX = regex.compile(r"<@(\d{15,23})>")
    # __slots___ would have no effect here, since commands.Context has no slots itself

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_author_id = self.author.id

    async def okay(self, *, ignore_error:bool=False):
        """Adds the okay hand reaction to the message"""

        try:
            await self.message.add_reaction("\N{OK HAND SIGN}")
        except discord.Forbidden as e:
            if ignore_error:
                return
            raise e

    @property
    def family_guild_id(self):
        """Returns the guild ID that should be used for family databases in this guild"""

        if self.bot.is_server_specific:
            return self.guild.id
        return 0

    def _set_footer(self, embed:discord.Embed) -> discord.Embed:
        """Sets the custom footer for the embed based on the bot config"""

        # Get footer from config
        try:
            possible_footer_objects = [[i] * i.get('amount', 1) for i in self.bot.config['footer']]  # Get from config
            footer_text_amount = []  # Make list for text
            [footer_text_amount.extend(i) for i in possible_footer_objects]  # Flatten list
            footer_text = [{'text': i['text']} for i in footer_text_amount]  # Remove 'amount'
            if len(footer_text) == 0:
                footer_text = self.DEFAULT_FOOTER_TEXT.copy()
        except Exception:
            footer_text = self.DEFAULT_FOOTER_TEXT.copy()

        # Grab random text from list
        footer = random.choice(footer_text)
        footer.update({'icon_url': self.bot.user.avatar_url})

        # Add and return
        footer['text'] = footer['text'].replace('{prefix}', self.prefix).replace(f"<@!{self.bot.user.id}> ", f"<@{self.bot.user.id}> ").replace(f"<@{self.bot.user.id}> ", f"@{self.bot.user!s} ")
        embed.set_footer(**footer)
        return embed

    async def send(self, content=None, *, tts=False, embed=None, file=None, files=None, delete_after=None, nonce=None, embeddify:bool=True, embed_image:bool=True, ignore_error:bool=False, image_url:str=None):
        """A custom version of Context that changes .send to embed things for me"""

        # Check the permissions we have
        try:
            channel_permissions: discord.Permissions = self.channel.permissions_for(self.guild.me)
            missing_permissions = channel_permissions.is_superset(self.DESIRED_PERMISSIONS)
        except AttributeError:
            missing_permissions = False
        no_embed = any([
            missing_permissions,
            embeddify is False,
            not isinstance(self.channel, discord.TextChannel),
        ])

        # Can't embed? Just send it normally
        if no_embed:
            try:
                return await super().send(
                    content=content,
                    tts=tts,
                    embed=embed,
                    file=file,
                    files=files,
                    delete_after=delete_after,
                    nonce=nonce,
                )
            except Exception as e:
                if not ignore_error:
                    raise e
                return

        # No current embed, and we _want_ to embed it? Alright!
        if embed is None and embeddify:
            # Set content
            embed = discord.Embed(description=content, colour=random.randint(1, 0xffffff))
            embed = self._set_footer(embed)
            if image_url:
                embed.set_image(url=image_url)

            # Set image
            if file and embed_image:
                file_is_image = any(
                    file.filename.casefold().endswith('.png'),
                    file.filename.casefold().endswith('.jpg'),
                    file.filename.casefold().endswith('.jpeg'),
                    file.filename.casefold().endswith('.gif'),
                    file.filename.casefold().endswith('.webm')
                )
                if file_is_image:
                    embed.set_image(url=f"attachment://{file.filename}")

            # Reset content
            content = self.bot.config.get("embed_default_text") or None

        # Send off our content
        try:
            return await super().send(
                content=content,
                tts=tts,
                embed=embed,
                file=file,
                files=files,
                delete_after=delete_after,
                nonce=nonce,
            )
        except Exception as e:
            if not ignore_error:
                raise e
            return

    @property
    def clean_prefix(self):
        """The prefix used but cleaned up for if it's a mention"""

        return self.USER_ID_REGEX.sub(
            lambda m: "@" + self.bot.get_member(int(m.group(1))).name,
            self.prefix
        )
