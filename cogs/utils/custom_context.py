from random import randint, choice

from discord import Embed, TextChannel, Permissions
from discord.ext.commands import Context


class NoOutputContext(Context):

    async def send(self, *args, **kwargs):
        pass


class CustomContext(Context):


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_author_id = self.author.id


    @property 
    def family_guild_id(self):
        '''Returns the guild ID that should be used for family databases in this guild'''

        if self.bot.is_server_specific:
            return self.guild.id
        return 0
        # return self.guild.id if self.guild.id in self.bot.server_specific_families else 0


    def _set_footer(self, embed:Embed):
        '''Sets the custom footer for the embed based on the bot config'''

        # Set footer
        try:
            possible_footer_objects = [[i] * i.get('amount', 1) for i in self.bot.config['footer']]  # Get from config
            footer_text_amount = []  # Make list for text 
            [footer_text_amount.extend(i) for i in possible_footer_objects]  # Flatten list
            footer_text = [{'text': i['text']} for i in footer_text_amount]  # Remove 'amount'

            # Make sure it's not empty
            if len(footer_text) == 0:
                raise Exception('Make default text')
        except Exception:
            footer_text = [{'text': 'MarriageBot'}]
        footer = choice(footer_text)
        footer.update({'icon_url': self.bot.user.avatar_url})
        footer['text'] = footer['text'].replace('{prefix}', self.prefix).replace(f"<@!{self.bot.user.id}> ", f"<@{self.bot.user.id}> ").replace(f"<@{self.bot.user.id}> ", f"@{self.bot.user!s} ")
        embed.set_footer(**footer)
        return embed


    async def send(self, content=None, *, tts=False, embed=None, file=None, files=None, delete_after=None, nonce=None, embeddify:bool=True, embed_image:bool=True, ignore_error:bool=False, image_url:str=None):
        '''
        A custom version of Context that changes .send to embed things for me
        '''

        try: x = self.channel.permissions_for(self.guild.me).value & 18432 != 18432
        except AttributeError: x = False
        no_embed = any([
            x,
            embeddify is False,
            not isinstance(self.channel, TextChannel),
        ])
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
                if not ignore_error: raise e

        if embed is None and embeddify:
            # Set content
            embed = Embed(description=content, colour=randint(1, 0xffffff))
            embed = self._set_footer(embed)
            if image_url:
                embed.set_image(url=image_url)

            # Set image
            if file and embed_image:
                if file.filename.casefold().endswith('.png') or file.filename.casefold().endswith('.jpg') or file.filename.casefold().endswith('.jpeg') or file.filename.casefold().endswith('.gif') or file.filename.casefold().endswith('.webm'):
                    embed.set_image(url=f"attachment://{file.filename}")

            # Reset content
            content = self.bot.config.get("embed_default_text") or None

        elif embed and embeddify:
            if embed.footer.text:
                pass 
            else:
                embed = self._set_footer(embed)

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
            if not ignore_error: raise e

    @property
    def clean_prefix(self):
        '''The prefix used but cleaned up for if it's a mention'''

        v = self.prefix 
        if '<@' in v:
            uid = int(v.split('>')[0].split('<@')[0])
            return f'@{self.bot.get_user(uid)[:5]}'
        return v
