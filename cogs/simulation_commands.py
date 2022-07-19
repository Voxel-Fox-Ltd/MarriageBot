from __future__ import annotations

import random
from typing import Optional

import discord
from discord.ext import commands, vbu


class SimulationCommands(vbu.Cog):

    async def get_reaction_gif(
            self,
            ctx: vbu.Context,
            reaction_type: Optional[str] = None,
            *,
            nsfw: bool = False,
            ignore_checks: bool = False) -> Optional[str]:
        """
        Gets a reaction gif from the Weeb.sh API.

        Parameters
        ----------
        ctx : vbu.Context
            The context for the command.
        reaction_type : Optional[str], optional
            The type of reaction that you want to get. If not provided, then the name of the command
            in the context is used.
        nsfw : bool, optional
            Whether or not to include NSFW results.
        ignore_checks : bool, optional
            Whether or not to ignore guild checks.

        Returns
        -------
        Optional[str]
            The GIF url.
        """

        # Make sure at least some of the attrs are set
        if reaction_type is None:
            assert ctx.command is not None
            reaction_type = ctx.command.name

        # See if we should return anything anyway
        if not ignore_checks:
            if not ctx.guild:
                return None
            if not self.bot.guild_settings[ctx.guild.id]['gifs_enabled']:
                return None

        # Make sure we have an API key
        if not self.bot.config.get('api_keys', {}).get('weebsh'):
            self.logger.debug("No API key set for Weeb.sh")
            return None

        # If we can't return images, then don't
        elif ctx.guild and not ctx.channel.permissions_for(ctx.guild.me).embed_links:  # type: ignore
            return None

        # Set up our headers and params
        headers = {
            "User-Agent": self.bot.user_agent,
            "Authorization": f"Wolke {self.bot.config['api_keys']['weebsh']}"
        }
        params = {
            "type": reaction_type,
            "nsfw": str(nsfw).lower(),
        }

        # Make the request
        async with self.bot.session.get(
                "https://api.weeb.sh/images/random",
                params=params, headers=headers) as r:
            try:
                data = await r.json()
            except Exception as e:
                data = await r.text()
                self.logger.warning(f"Error from Weeb.sh ({e}): {str(data)}")
                return None
            if r.ok:
                return data['url']
        return None

    @commands.command(
        aliases=['snuggle', 'cuddle'],
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="user",
                    description="The user you want to hug.",
                    type=discord.ApplicationCommandOptionType.user,
                ),
            ],
        ),
    )
    @commands.defer()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def hug(
            self,
            ctx: vbu.Context,
            user: discord.Member):
        """
        Hugs a mentioned user.
        """

        if user == ctx.author:
            return await ctx.send("*You hug yourself... and start crying.*")
        image_url = await self.get_reaction_gif(ctx)
        await vbu.embeddify(ctx, f"*Hugs {user.mention}.*", image_url=image_url)

    @commands.command(
        aliases=['smooch', 'makeout'],
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="user",
                    description="The user you want kiss.",
                    type=discord.ApplicationCommandOptionType.user,
                ),
            ],
        ),
    )
    @commands.defer()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def kiss(
            self,
            ctx: vbu.Context,
            user: discord.Member):
        """
        Kisses a mentioned user.
        """

        if user == ctx.author:
            return await ctx.send("How would you even manage to do that?")
        image_url = await self.get_reaction_gif(ctx)
        await vbu.embeddify(ctx, f"*Kisses {user.mention}.*", image_url=image_url)

    @commands.command(
        aliases=['smack'],
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="user",
                    description="The user you want slap.",
                    type=discord.ApplicationCommandOptionType.user,
                ),
            ],
        ),
    )
    @commands.defer()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def slap(
            self,
            ctx: vbu.Context,
            user: discord.Member):
        """
        Slaps a mentioned user.
        """

        if user == ctx.author:
            return await ctx.send("*You slapped yourself... for some reason.*")
        image_url = await self.get_reaction_gif(ctx)
        await vbu.embeddify(ctx, f"*Slaps {user.mention}.*", image_url=image_url)

    @commands.command(
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="user",
                    description="The user you want punch.",
                    type=discord.ApplicationCommandOptionType.user,
                ),
            ],
        ),
    )
    @commands.defer()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def punch(
            self,
            ctx: vbu.Context,
            user: discord.Member):
        """
        Punches a mentioned user.
        """

        if user == ctx.author:
            return await ctx.send("*You punched yourself... for some reason.*")
        image_url = await self.get_reaction_gif(ctx)
        await vbu.embeddify(ctx, f"*Punches {user.mention} right in the nose.*", image_url=image_url)

    @commands.command(
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="user",
                    description="The user you want stab.",
                    type=discord.ApplicationCommandOptionType.user,
                ),
            ],
        ),
    )
    @commands.defer()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def stab(
            self,
            ctx: vbu.Context,
            user: discord.Member):
        """
        Stabs a mentioned user.
        """

        if user == ctx.author:
            responses = [
                "You stab yourself.",
                "Looks like you don't have a knife, oops!",
                "No.",
            ]
        else:
            responses = [
                f"You stab {user.mention}.",
                f"{user.mention} has been stabbed.",
                f"*stabs {user.mention}.*",
                "Looks like you don't have a knife, oops!",
                "You can't legally stab someone without thier consent.",
                "Stab? Isn't that, like, illegal?",
                "I wouldn't recommend doing that tbh.",
            ]
        await ctx.send(random.choice(responses))

    @commands.command(
        aliases=['murder'],
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="user",
                    description="The user you want murder.",
                    type=discord.ApplicationCommandOptionType.user,
                ),
            ],
        ),
    )
    @commands.defer()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def kill(
            self,
            ctx: vbu.Context,
            user: Optional[discord.Member] = None):
        """
        Kills a person :/
        """

        responses = [
            "That would violate at least one of the laws of robotics.",
            "I am a text-based bot. I cannot kill.",
            "Unfortunately, murder isn't supported in this version of MarriageBot.",
            "Haha good joke there, but I'd never kill a person! >.>",
            "To my knowledge, you can't kill via the internet. Let me know when that changes.",
            "I am designed to bring people together, not murder them.",
        ]
        await ctx.send(random.choice(responses))


def setup(bot: vbu.Bot):
    x = SimulationCommands(bot)
    bot.add_cog(x)
