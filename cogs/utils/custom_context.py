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
        no_embed = any([
            self.channel.permissions_for(self.guild.me).value & 18432 != 18432,
            embeddify is False,
            not isinstance(self.channel, TextChannel),
        ])
        if no_embed:
            try: 
                await original
            except Exception as e:
                if not ignore_error: raise e

        if embed is None and embeddify:
            # Set content
            embed = Embed(description=content, colour=randint(1, 0xffffff))

            # Set footer
            extra = [{'text': 'MarriageBot'}] * 20
            extra += [
                {'text': 'MarriageBot - Made by Caleb#2831'},
                {'text': f'MarriageBot - Add me to your own server! ({self.prefix}invite)'}
            ]
            if self.bot.config.get('dbl_token'):
                extra.append({'text': f'MarriageBot - Add a vote on Discord Bot List! ({self.prefix}vote)'})
            if self.bot.config.get('patreon'):
                extra.append({'text': f'MarriageBot - Support me on Patreon! ({self.prefix}patreon)'})
            if self.bot.config.get('guild'):
                extra.append({'text': f'MarriageBot - Join the official Discord server! ({self.prefix}server)'})
            footer = choice(extra)
            footer.update({'icon_url': self.bot.user.avatar_url})
            footer['text'] = footer['text'].replace(f"<@!{self.bot.user.id}> ", f"<@{self.bot.user.id}> ").replace(f"<@{self.bot.user.id}> ", f"@{self.bot.user!s} ")
            embed.set_footer(**footer)

            # Set image
            if file and embed_image:
                if file.filename.casefold().endswith('.png') or file.filename.casefold().endswith('.jpg') or file.filename.casefold().endswith('.jpeg') or file.filename.casefold().endswith('.gif') or file.filename.casefold().endswith('.webm'):
                    embed.set_image(url=f"attachment://{file.filename}")

            # Reset content
            content = self.bot.config.get("embed_default_text") or None

        try:
            await super().send(
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
