from random import randint, choice

from discord import Embed, TextChannel, Permissions
from discord.ext.commands import Context


class CustomContext(Context):

    async def send(self, content=None, *, tts=False, embed=None, file=None, files=None, delete_after=None, nonce=None, embeddify:bool=True, embed_image:bool=True, ignore_error:bool=False):
        '''
        A custom version of Context that changes .send to embed things for me
        '''

        original = super().send(
            content=content, 
            tts=tts, 
            embed=embed, 
            file=file, 
            files=files, 
            delete_after=delete_after, 
            nonce=nonce,
        )
        try: x = self.channel.permissions_for(self.guild.me).value & 18432 != 18432
        except AttributeError: x = False
        no_embed = any([
            x,
            embeddify is False,
            not isinstance(self.channel, TextChannel),
        ])
        if no_embed:
            try: 
                return await original
            except Exception as e:
                if not ignore_error: raise e

        if embed is None and embeddify:
            # Set content
            embed = Embed(description=content, colour=randint(1, 0xffffff))

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

            # Set image
            if file and embed_image:
                if file.filename.casefold().endswith('.png') or file.filename.casefold().endswith('.jpg') or file.filename.casefold().endswith('.jpeg') or file.filename.casefold().endswith('.gif') or file.filename.casefold().endswith('.webm'):
                    embed.set_image(url=f"attachment://{file.filename}")

            # Reset content
            content = self.bot.config.get("embed_default_text") or None

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
