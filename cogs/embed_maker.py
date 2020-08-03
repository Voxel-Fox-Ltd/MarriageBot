import asyncio
import json

import discord
from discord.ext import commands

from cogs import utils


class EmbedMaker(utils.Cog, command_attrs={'hidden': True}):

    def __init__(self, bot:utils.Bot):
        super().__init__(bot)
        self.last_made_embed = {}

    @commands.command(cls=utils.Command)
    @commands.is_owner()
    @commands.bot_has_permissions(send_messages=True)
    async def makeembed(self, ctx, *, data:str=None):
        """Run a command as another user optionally in another channel."""

        # See if we gave some JSON
        if data:
            json_data = json.loads(data)
            return await self.send_embed(ctx, ctx.author, json_data.get('content'), json_data.get('embed', {}))

        # Looks like we gotta do it the hard way
        user = ctx.author
        content = None
        embed = {"fields": []}
        await ctx.okay()

        # These are our instructions
        INSTRUCTIONS = [
            "1\N{combining enclosing keycap} Set content",
            "2\N{combining enclosing keycap} Add field",
            "3\N{combining enclosing keycap} Set author",
            "4\N{combining enclosing keycap} Set footer",
            "5\N{combining enclosing keycap} Set image",
            "6\N{combining enclosing keycap} Set thumbnail",
            "7\N{combining enclosing keycap} Set description",
            "8\N{combining enclosing keycap} Set colour",
            "9\N{combining enclosing keycap} Done",
            "0\N{combining enclosing keycap} Load last created embed",
        ]

        # These are the associated methods
        METHOD_EMOJI = {
            "1\N{combining enclosing keycap}": self.embed_set_content,
            "2\N{combining enclosing keycap}": self.embed_add_field,
            "3\N{combining enclosing keycap}": self.embed_set_author,
            "4\N{combining enclosing keycap}": self.embed_set_footer,
            "5\N{combining enclosing keycap}": self.embed_set_image,
            "6\N{combining enclosing keycap}": self.embed_set_thumbnail,
            "7\N{combining enclosing keycap}": self.embed_set_description,
            "8\N{combining enclosing keycap}": self.embed_set_colour,
            "9\N{combining enclosing keycap}": None,
            "0\N{combining enclosing keycap}": self.load_last_created_embed,
        }

        # Loop through and make our embed
        while True:
            instruction_message = await user.send('\n'.join(INSTRUCTIONS))
            for e in METHOD_EMOJI.keys():
                await instruction_message.add_reaction(e)
            check = lambda r, u: r.message.channel == instruction_message.channel and u.id == ctx.author.id  # noqa: E731
            try:
                reaction, _ = await self.bot.wait_for("reaction_add", check=check, timeout=120)
            except asyncio.TimeoutError:
                return await user.send("Timed out. Cancelling embed creation.")
            emoji = str(reaction)

            # Find which method to run
            method = METHOD_EMOJI.get(emoji)
            if method is None:
                await self.send_embed(ctx, user, content, embed)
                break

            # Update our stored data
            data = await method(user, content, embed)
            if data is not None:
                content, new_embed = data

                # Send preview
                try:
                    await user.send(content, embed=discord.Embed.from_dict(new_embed) if embed else None)
                    embed = new_embed
                except Exception as e:
                    await user.send(f"Found an error sending that preview, reverting data - {e!s}")
                    await user.send(content, embed=discord.Embed.from_dict(embed) if embed else None)

    async def embed_set_content(self, user:discord.User, content:str, embed:dict):
        """Update the content that would be sent"""

        await user.send("What do you want to set the **message content** as (`skip` to remove)?")
        message = await self.bot.wait_for("message", check=lambda m: m.channel == user.dm_channel and not m.author.bot)
        content = message.content
        if content.lower() == 'skip':
            content = None
        return content, embed

    async def embed_add_field(self, user:discord.User, content:str, embed:dict):
        """Update the fields in the embed"""

        await user.send("What's the **name** for this field?")
        name_message = await self.bot.wait_for("message", check=lambda m: m.channel == user.dm_channel and not m.author.bot)
        await user.send("What's the **value** for this field?")
        value_message = await self.bot.wait_for("message", check=lambda m: m.channel == user.dm_channel and not m.author.bot)
        await user.send("Do you want to set this field as **inline** (yes/no)?")
        inline_message = await self.bot.wait_for("message", check=lambda m: m.channel == user.dm_channel and not m.author.bot)
        embed['fields'].append({
            "name": name_message.content,
            "value": value_message.content,
            "inline": inline_message.content.lower() == "yes",
        })
        return content, embed

    async def embed_set_author(self, user:discord.User, content:str, embed:dict):
        """Update the embed's author"""

        await user.send("What's the **name** for this field (`skip` to remove)?")
        name_message = await self.bot.wait_for("message", check=lambda m: m.channel == user.dm_channel and not m.author.bot)
        if name_message.content.lower() == 'skip':
            embed.pop('author')
            return content, embed
        await user.send("What's the **icon URL** for this field (or `skip`)?")
        icon_url_message = await self.bot.wait_for("message", check=lambda m: m.channel == user.dm_channel and not m.author.bot)
        await user.send("What's the **URL** for this field (or `skip`)?")
        url_message = await self.bot.wait_for("message", check=lambda m: m.channel == user.dm_channel and not m.author.bot)
        embed['author'] = {
            "name": name_message.content,
            "icon_url": icon_url_message.content if icon_url_message.content.lower() != "skip" else None,
            "url": url_message.content if url_message.content.lower() != "skip" else None,
        }
        return content, embed

    async def embed_set_footer(self, user:discord.User, content:str, embed:dict):
        """Update the embed's footer"""

        await user.send("What's the **name** for this field (`skip` to remove)?")
        name_message = await self.bot.wait_for("message", check=lambda m: m.channel == user.dm_channel and not m.author.bot)
        if name_message.content.lower() == 'skip':
            embed.pop('footer')
            return content, embed
        await user.send("What's the **icon URL** for this field (or `skip`)?")
        icon_url_message = await self.bot.wait_for("message", check=lambda m: m.channel == user.dm_channel and not m.author.bot)
        embed['footer'] = {
            "text": name_message.content,
            "icon_url": icon_url_message.content if icon_url_message.content.lower() != "skip" else None,
        }
        return content, embed

    async def embed_set_image(self, user:discord.User, content:str, embed:dict):
        """Update the embed's image"""

        await user.send("What's the **URL** for this field (`skip` to remove)?")
        name_message = await self.bot.wait_for("message", check=lambda m: m.channel == user.dm_channel and not m.author.bot)
        embed['image'] = {
            "url": name_message.content,
        }
        if name_message.content.lower() == 'skip':
            embed.pop('image')
        return content, embed

    async def embed_set_thumbnail(self, user:discord.User, content:str, embed:dict):
        """Update the embed's thumbnail"""

        await user.send("What's the **URL** for this field (`skip` to remove)?")
        name_message = await self.bot.wait_for("message", check=lambda m: m.channel == user.dm_channel and not m.author.bot)
        embed['thumbnail'] = {
            "url": name_message.content,
        }
        if name_message.content.lower() == 'skip':
            embed.pop('thumbnail')
        return content, embed

    async def embed_set_description(self, user:discord.User, content:str, embed:dict):
        """Update the embed's description"""

        await user.send("What's the **text** for this field (`skip` to remove)?")
        name_message = await self.bot.wait_for("message", check=lambda m: m.channel == user.dm_channel and not m.author.bot)
        embed['description'] = name_message.content
        if name_message.content.lower() == 'skip':
            embed.pop('description')
        return content, embed

    async def embed_set_colour(self, user:discord.User, content:str, embed:dict):
        """Update the embed's colour"""

        await user.send("What **hex colour** do you want to set your embed to (`skip` to remove)?")
        colour_message = await self.bot.wait_for("message", check=lambda m: m.channel == user.dm_channel and not m.author.bot)
        if colour_message.content.lower() == 'skip':
            embed.pop('color')
            return content, embed
        try:
            embed['color'] = int(colour_message.content.strip('# '), 16)
        except ValueError:
            await user.send("I couldn't convert that to a hex number.")
            return None
        return content, embed

    async def send_embed(self, ctx:utils.Context, user:discord.User, content:str, embed:dict):
        """Send out the embed to wherever ya want babey"""

        # Store last made embed
        self.last_made_embed[user.id] = {'content': content, 'embed': embed}

        # Find the destination
        await user.send("Where do you want to send this embed (or `skip`)?")
        message = await self.bot.wait_for("message", check=lambda m: m.channel == user.dm_channel and not m.author.bot)
        channel = None
        try:
            channel = await commands.TextChannelConverter().convert(ctx, message.content)
        except commands.CommandError:
            if message.content.lower() != 'skip':
                return await user.send("Alright, skpping.")
            return await user.send("I can't work out where you want to send that. Sorry about that. Cancelled.")
        if channel is None:
            return await user.send("Found an error sending that. Sorry about that. Cancelled.")

        # Send it out
        if embed and embed != {"fields": []}:
            embed_object = discord.Embed.from_dict(embed)
        else:
            embed_object = None
        sent_message = await channel.send(content, embed=embed_object)
        return await user.send(f"Done! c:\n{sent_message.jump_url}")

    async def load_last_created_embed(self, user, content, embed):
        """Load up the last created embed"""

        last_data = self.last_made_embed.get(user.id)
        if not last_data:
            await user.send("You have no stored previous data.")
            return None
        return last_data['content'], last_data['embed']


def setup(bot:utils.Bot):
    x = EmbedMaker(bot)
    bot.add_cog(x)
