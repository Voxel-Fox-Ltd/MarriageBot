from __future__ import annotations

import random
from typing import Optional

import discord
from discord.ext import commands, vbu

from cogs import utils


PICKUP_LINES = (
    "Do you like raisins? How do you feel about a date?",
    "If I could rearrange the alphabet, I'd put \"U\" and \"I\" together.",
    "Are you a parking ticket? Because you've got FINE written all over you.",
    "Are you from Tennessee? Because you're the only 10 I see!",
    "Are you French? Because Eiffel for you.",
    "I'm no photographer, but I can picture us together.",
    "Are you Australian? Because you meet all of my koala-fications.",
    "Are you a magician? When I look at you everything disappears.",
    "There's something wrong with my phone. It doesn't have your number in it.",
    "Are you religious? Cause you're the answer to all my prayers.",
    "Do you like coffee? Because I like you a latte.",
    "If a star fell from the sky every time I thought about you, then tonight the sky would be empty.",
    "Is it hot in here? Or is it just you?",
    "I don't have a library card, but do you mind if I check you out?",
    "Are you the sun? I'm about to get a sunburn looking at you.",
    "Roses are red. Violets are blue. I didn't know what perfect was until I met you.",
    "You dropped something. My jaw.",
    "If you were words on a page, you'd be fine print.",
    "There must be something wrong with my eyes, I can't take them off you.",
    "Are you a bank loan? Because you got my interest. ",
    "Somebody call the cops, because it's got to be illegal to look that good!",
    "Do you know why it doesn't matter if there's gravity or not? Because I'd still fall for you.",
    "I must be a snowflake, because I've fallen for you.",
    "Are you a keyboard? Because you're my type.",
    "Do you have a map? I just got lost in your eyes.",
    "You know what's the worst thing that can happen to you right now? Me not dating you.",
    "I know you're busy today, but can you add me to your to-do list?",
    "If you were a steak you would be well done.",
    "You must be a broom because you swept me off my feet.",
    "Did it hurt when you fell from heaven?",
    "Come live in my heart, and pay no rent.",
    "Hello, I'm a thief, and I'm here to steal your heart.",
    "Have you always been this cute, or did you have to work at it?",
    "Are you cake? Cause I want a piece of that.",
    "Is it okay if I take a photo of you so I can show Santa what I want for Christmas?",
    "Did you just strike a match? I swear as soon as you walked in, it got lit.",
    "Do you have a New Year's resolution? Because I'm looking at mine right now.",
    "Are you lost? Heaven is a long way from here.",
    "There is something wrong with my phone. It doesn't have your number in it.",
    "If you were a library book, I would check you out.",
    "Your hand looks heavy. I can hold it for you!",
    "Are you a cat because I'm feline a connection between us",
    "If I were to ask you out on a date, would your answer be the same as the answer to this question?",
    "If nothing lasts forever, will you be my nothing?",
    "When God made you, he was showing off.",
    "I must be in a museum, because you truly are a work of art.",
    "You spend so much time in my mind, I should charge you rent.",
    "My lips are like skittles. Wanna taste the rainbow?",
    "Well, here I am. What were your other two wishes?",
    "Do I know you from somewhere? Oh, that's right. My dreams.",
    "If you were a tear in my eye I would not cry for fear of losing you.",
    "Life without you is like a broken pencil. Pointless.",
    "I'd rate you a nine because the only thing missing is me.",
    "They say that kissing is a language of love, so would you mind starting a conversation with me?",
    "I'm on top of things. Would you like to be one of them?",
    "If you were a fruit you'd be a fineapple.",
    "I'll give you a kiss. If you don't like it, you can return it.",
    "Did you swallow magnets? Cause you're attractive.",
    "Do you have a name, or can I call you mine?",
    "Are you craving Pizza? Because I'd love to get a pizz-a you.",
    "Do you like science? Because I got my ion you.",
    "Wouldn't we look cute on a wedding cake together.",
    "Would you touch my hand so I can tell my friends I've been touched by an angel?",
    "There isn't a word in the dictionary for how good you look.",
    "You must be a ninja, because you snuck into my heart",
    "Can you pinch me? You're so fine I must be dreaming.",
    "Do you know what I would do if I was a surgeon? I'd give you my heart.",
    "I may not be a genie, but I can make all your wishes come true!",
    "Do you have an inhaler? You took my breath away.",
    "I'm learning about important dates in history. Wanna be one of them?",
)


class SimulationCommands(vbu.Cog[utils.types.Bot]):

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
            The type of reaction that you want to get. If not provided,
            then the name of the command in the context is used.
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
        if not hasattr(ctx, "interaction") and ctx.guild and not ctx.channel.permissions_for(ctx.guild.me).embed_links:  # type: ignore
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
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def stab(
            self,
            ctx: vbu.SlashContext,
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
                "You can't legally stab someone without their consent.",
                "Stab? Isn't that, like, illegal?",
                "I wouldn't recommend doing that tbh.",
            ]
        await ctx.interaction.response.send_message(random.choice(responses))

    # @commands.command(
    #     aliases=['murder'],
    #     application_command_meta=commands.ApplicationCommandMeta(
    #         options=[
    #             discord.ApplicationCommandOption(
    #                 name="user",
    #                 description="The user you want murder.",
    #                 type=discord.ApplicationCommandOptionType.user,
    #             ),
    #         ],
    #     ),
    # )
    # @commands.cooldown(1, 3, commands.BucketType.user)
    # @commands.bot_has_permissions(send_messages=True)
    # async def kill(
    #         self,
    #         ctx: vbu.SlashContext,
    #         user: discord.Member):
    #     """
    #     Kills a person :/
    #     """

    #     responses = [
    #         "That would violate at least one of the laws of robotics.",
    #         "I am a text-based bot. I cannot kill.",
    #         "Unfortunately, murder isn't supported in this version of MarriageBot.",
    #         "Haha good joke there, but I'd never kill a person! >.>",
    #         "To my knowledge, you can't kill via the internet. Let me know when that changes.",
    #         "I am designed to bring people together, not murder them.",
    #         f"*Kills {user.mention}*.",
    #         f"You have successfully murdered {user.mention}.",
    #     ]
    #     await ctx.interaction.response.send_message(random.choice(responses))

    @commands.command(
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="user",
                    description="The user you want bite.",
                    type=discord.ApplicationCommandOptionType.user,
                ),
            ],
        ),
    )
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def bite(
            self,
            ctx: vbu.SlashContext,
            user: discord.Member):
        """
        Bites you bites you bites you.
        """

        if user == ctx.author:
            responses = [
                "You missed and bit yourself! Loser.",
                f"You failed to bite {user.mention}!",
                "You thought! You bit yourself.",
                "We'll act like you didn't just bite yourself.",
                "Your aim is terrible, you bit yourself instead.",
            ]
        else:
            responses = [
                f"You bite {user.mention}.",
                f"*Bites {user.mention}.*",
                f"{user.mention} was bitten.",
                f"{user.mention} has been bitten.",
                "Why would you bite someone?",
                "Biting people isn’t nice.",
                "Stop biting people!",
            ]
        await ctx.interaction.response.send_message(random.choice(responses))

    @commands.command(
        application_command_meta=commands.ApplicationCommandMeta(),
    )
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def pickup(
            self,
            ctx: vbu.SlashContext):
        """
        Gives you a random pickup line :)
        """

        await ctx.interaction.response.send_message(random.choice(PICKUP_LINES))


def setup(bot: utils.types.Bot):
    x = SimulationCommands(bot)
    bot.add_cog(x)
