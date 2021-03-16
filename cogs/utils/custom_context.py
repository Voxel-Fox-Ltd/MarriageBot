import random

import discord
from discord.ext import commands


class CustomContext(commands.Context):
    """A custom subclass of commands.Context that embeds all content"""

    DESIRED_PERMISSIONS = discord.Permissions(18432)  # embed links, send messages
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
            possible_footer_objects = [[i] * i.get('amount', 1) for i in self.bot.config['embed']['footer']]  # Get from config
            footer_text_amount = []  # Make list for text
            [footer_text_amount.extend(i) for i in possible_footer_objects]  # Flatten list
            footer_text = [{'text': i['text']} for i in footer_text_amount]  # Remove 'amount'
            if len(footer_text) == 0:
                footer_text = None
            if self.bot.config['embed']['add_footer'] is False:
                footer_text = None
        except Exception:
            footer_text = None

        # Don't add a footer if there isn't any
        if footer_text is None:
            return embed

        # Grab random text from list
        footer = random.choice(footer_text)
        footer.update({'icon_url': self.bot.user.avatar_url})

        # Add and return
        footer['text'] = footer['text'].replace('{prefix}', self.prefix).replace(f"<@!{self.bot.user.id}> ", f"<@{self.bot.user.id}> ").replace(f"<@{self.bot.user.id}> ", f"@{self.bot.user!s} ")
        embed.set_footer(**footer)
        return embed

    async def send(
            self, content=None, *, tts=False, embed=None, file=None, files=None, delete_after=None, nonce=None, embeddify:bool=True,
            embed_image:bool=True, ignore_error:bool=False, image_url:str=None,
            allowed_mentions:discord.AllowedMentions=discord.AllowedMentions.none()):
        """A custom version of Context that changes .send to embed things for me"""

        # Check the permissions we have
        try:
            channel_permissions: discord.Permissions = self.channel.permissions_for(self.guild.me)
            missing_permissions = not self.DESIRED_PERMISSIONS.is_subset(channel_permissions)
        except AttributeError:
            missing_permissions = False
        no_embed = any([
            missing_permissions,
            embeddify is False,
            not isinstance(self.channel, (discord.TextChannel, discord.DMChannel)),
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
                    allowed_mentions=allowed_mentions,
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
                file_is_image = any([
                    file.filename.casefold().endswith('.png'),
                    file.filename.casefold().endswith('.jpg'),
                    file.filename.casefold().endswith('.jpeg'),
                    file.filename.casefold().endswith('.gif'),
                    file.filename.casefold().endswith('.webm')
                ])
                if file_is_image:
                    embed.set_image(url=f"attachment://{file.filename}")

            # Reset content
            content = self.bot.config.get("embed", dict()).get("content") or None

            # Set author
            author_data = self.bot.config.get("embed", dict()).get("author") or None
            if author_data:
                author_name = author_data.get("name") or None
                author_url = author_data.get("url") or None
                if author_name and author_url:
                    embed.set_author(name=author_name, url=author_url, icon_url=self.bot.user.avatar_url)
                elif author_name:
                    embed.set_author(name=author_name, icon_url=self.bot.user.avatar_url)

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
