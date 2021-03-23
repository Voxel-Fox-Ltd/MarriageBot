import random
import asyncio
import typing

import discord
from discord.ext import commands
import voxelbotutils as utils

from cogs import utils as localutils


class SimulationCommands(utils.Cog):
    """
    This cog is pretty much just a command and a response, it handles the GIF commands (m!kiss, slap, etc),
    but otherwise this is just some fun commands.
    """

    async def get_reaction_gif(self, ctx:utils.Context, reaction_type:str=None, *, nsfw:bool=False) -> typing.Optional[str]:
        """
        Gets a reaction gif from the Weeb.sh API.
        """

        # See if we should return anything anyway
        if not self.bot.guild_settings[ctx.guild.id]['gifs_enabled']:
            return None

        # Make sure we have an API key
        if not self.bot.config.get('api_keys', {}).get('weebsh'):
            self.logger.debug("No API key set for Weeb.sh")
            return None

        # Set up our headers and params
        headers = {
            "User-Agent": self.bot.user_agent,
            "Authorization": f"Wolke {self.bot.config['api_keys']['weebsh']}"
        }
        params = {
            "type": reaction_type or ctx.command_name,
            "nsfw": str(nsfw).lower(),
        }

        # Make the request
        async with self.bot.session.get("https://api.weeb.sh/images/random", params=params, headers=headers) as r:
            try:
                data = await r.json()
            except Exception as e:
                data = await r.text()
                self.logger.warning(f"Error from Weeb.sh ({e}): {str(data)}")
                return None
            if 300 > r.status >= 200:
                return data['url']
        return None

    @utils.command(aliases=['snuggle', 'cuddle'])
    @utils.cooldown.cooldown(1, 5, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def hug(self, ctx:utils.Context, user:discord.Member):
        """
        Hugs a mentioned user.
        """

        if user == ctx.author:
            return await ctx.send("*You hug yourself... and start crying.*")
        image_url = await self.get_reaction_gif(ctx)
        await ctx.send(f"*Hugs {user.mention}.*", image_url=image_url)

    @utils.command(aliases=['smooch'])
    @utils.cooldown.cooldown(1, 5, commands.BucketType.user)
    @utils.checks.bot_is_ready()
    @commands.bot_has_permissions(send_messages=True)
    async def kiss(self, ctx:utils.Context, user:discord.Member):
        """
        Kisses a mentioned user.
        """

        if user == ctx.author:
            return await ctx.send("How would you even manage to do that?")
        image_url = await self.get_reaction_gif(ctx)
        await ctx.send(f"*Kisses {user.mention}.*", image_url=image_url)

    @utils.command(aliases=['smack'])
    @utils.cooldown.cooldown(1, 5, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def slap(self, ctx:utils.Context, user:discord.Member):
        """
        Slaps a mentioned user.
        """

        if user == ctx.author:
            return await ctx.send("*You slapped yourself... for some reason.*")
        image_url = await self.get_reaction_gif(ctx)
        await ctx.send(f"*Slaps {user.mention}.*", image_url=image_url)

    @utils.command()
    @utils.cooldown.cooldown(1, 5, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def coffee(self, ctx:utils.Context, user:discord.Member=None):
        """
        Gives coffee to a mentioned user.
        """

        if user == ctx.author:
            return await ctx.send("*You spilled coffee all over yourself... for some reason.*")
        if user is None:
            responses = [
                "You make coffee.",
                "You try to make coffee, but forgot the cup.",
                "You make coffee... then cry.",
                "This is awkward... You forgot to pay the water bill.",
                "You made coffee. Congrats.",
            ]
            return await ctx.send(random.choice(responses))
        await ctx.send(f"*Gives coffee to {user.mention}.*")

    @utils.command()
    @utils.cooldown.cooldown(1, 5, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def punch(self, ctx:utils.Context, user:discord.Member):
        """
        Punches a mentioned user.
        """

        if user == ctx.author:
            return await ctx.send("*You punched yourself... for some reason.*")
        image_url = await self.get_reaction_gif(ctx)
        await ctx.send(f"*Punches {user.mention} right in the nose.*", image_url=image_url)

    @utils.command(hidden=True)
    @utils.cooldown.cooldown(1, 5, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def cookie(self, ctx:utils.Context, user:discord.Member):
        """
        Gives a cookie to a mentioned user.
        """

        if user == ctx.author:
            return await ctx.send("*You gave yourself a cookie.*")
        await ctx.send(f"*Gives {user.mention} a cookie.*")

    @utils.command(aliases=['nunget', 'nuggie'], hidden=True)
    @utils.cooldown.cooldown(1, 5, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True, use_external_emojis=True)
    async def nugget(self, ctx:utils.Context, user:discord.Member):
        """
        Gives a nugget to a mentioned user.
        """

        if user == ctx.author:
            return await ctx.send(f"*You give yourself a {ctx.invoked_with}* <:nugget:585626539605884950>")
        await ctx.send(f"*Gives {user.mention} a {ctx.invoked_with}* <:nugget:585626539605884950>")

    @utils.command(aliases=['borger', 'borg'], hidden=True)
    @utils.cooldown.cooldown(1, 5, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def burger(self, ctx:utils.Context, user:discord.Member):
        """
        Gives a burger to a mentioned user.
        """

        if user == ctx.author:
            return await ctx.send(f"*You give yourself a {ctx.invoked_with}* 🍔")
        await ctx.send(f"*Gives {user.mention} a {ctx.invoked_with}* 🍔")

    @utils.command(hidden=True)
    @utils.cooldown.cooldown(1, 5, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def tea(self, ctx:utils.Context, user:discord.Member):
        """
        Gives tea to a mentioned user.
        """

        if user == ctx.author:
            return await ctx.send("*You gave yourself tea.*")
        await ctx.send(f"*Gives {user.mention} tea.*")

    @utils.command(aliases=['dumpster'], hidden=True)
    @utils.cooldown.cooldown(1, 5, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def garbage(self, ctx:utils.Context, user:discord.Member):
        """
        Throws a user in the garbage.
        """

        if user == ctx.author:
            return await ctx.send("*You climb right into the trash can, where you belong.*")
        await ctx.send(f"*Throws {user.mention} into the dumpster.*")

    @utils.command(hidden=True)
    @utils.cooldown.cooldown(1, 5, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def poke(self, ctx:utils.Context, user:discord.Member):
        """
        Pokes a given user.
        """

        if user == ctx.author:
            return await ctx.send("You poke yourself.")
        image_url = await self.get_reaction_gif(ctx)
        await ctx.send(f"*Pokes {user.mention}.*", image_url=image_url)

    @utils.command(hidden=True)
    @utils.cooldown.cooldown(1, 5, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def stab(self, ctx:utils.Context, user:discord.Member):
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

    @utils.command(aliases=['murder'], hidden=True)
    @commands.bot_has_permissions(send_messages=True)
    async def kill(self, ctx:utils.Context, user:discord.Member=None):
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

    @utils.command(aliases=['vore'], hidden=True)
    @commands.bot_has_permissions(send_messages=True)
    async def eat(self, ctx:utils.Context, user:discord.Member):
        """
        Eats a person OwO
        """

        responses = [
            f"You swallowed {user.mention}... through the wrong hole.",
            f"You've eaten {user.mention}. Gross.",
            f"Are you into this or something? You've eaten {user.mention}.",
            f"I guess lunch wasnt good enough. You eat {user.mention}.",
            f"You insert {user.mention} into your mouth and proceed to digest them.",
        ]
        await ctx.send(random.choice(responses))

    @utils.command(hidden=True)
    @commands.bot_has_permissions(send_messages=True)
    async def sleep(self, ctx:utils.Context):
        """
        Todd Howard strikes once more.
        """

        await ctx.send((
            "You sleep for a while and when you wake up you're in a cart "
            "with your hands bound. A man says \"Hey, you. You're finally "
            "awake. You were trying to cross the border, right?\""
        ))

    @utils.command(aliases=['intercourse', 'fuck', 'smash', 'heck'], hidden=True, enabled=False)
    @utils.cooldown.cooldown(1, 5, commands.BucketType.user)
    @commands.is_nsfw()
    @utils.checks.bot_is_ready()
    @commands.bot_has_permissions(send_messages=True)
    async def copulate(self, ctx:utils.Context, user:discord.Member):
        """
        Lets you... um... heck someone.
        """

        # Check for the most common catches
        text_processor = localutils.random_text.RandomText('copulate', ctx.author, user)
        text = text_processor.process(check_for_instigator=False)
        if text:
            return await ctx.send(text)

        # Check if they are related
        x = localutils.FamilyTreeMember.get(ctx.author.id, ctx.family_guild_id)
        y = localutils.FamilyTreeMember.get(user.id, ctx.family_guild_id)
        async with ctx.channel.typing():
            relationship = x.get_relation(y)
        if relationship is None or relationship.casefold() == 'partner' or self.bot.allows_incest(ctx.guild.id):
            pass
        else:
            return await ctx.send(text_processor.target_is_family())

        # Ping out a message for them
        await ctx.send(text_processor.valid_target())

        # Wait for a response
        try:
            check = localutils.AcceptanceCheck(user.id, ctx.channel.id).check
            m = await self.bot.wait_for('message', check=check, timeout=60.0)
            response = check(m)
        except asyncio.TimeoutError:
            return await ctx.send(text_processor.request_timeout(), ignore_error=True)

        # Process response
        if response == "NO":
            return await ctx.send(text_processor.request_denied())
        await ctx.send(text_processor.request_accepted())

    @utils.command(hidden=True)
    @utils.cooldown.cooldown(1, 5, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def chocolate(self, ctx:utils.Context, user:discord.Member):
        """
        Gives chocolate to a mentioned user.
        """

        if user == ctx.author:
            return await ctx.send("*You bought some choclate.*")
        await ctx.send(f"*Gives {user.mention} chocolate.*")

    @utils.command(hidden=True)
    @utils.cooldown.cooldown(1, 5, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def wave(self, ctx:utils.Context, user:discord.Member=None):
        """
        Waves to someone
        """

        if user is None or user == ctx.author:
            return await ctx.send("*You wave to yourself... consider getting some friends.*")
        await ctx.send(f"*Waves to {user.mention} :wave:")

    @utils.command(hidden=True)
    @utils.cooldown.cooldown(1, 5, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def apple(self, ctx:utils.Context, user:discord.Member):
        """
        Gives a apple to a mentioned user.
        """

        if user == ctx.author:
            return await ctx.send("*You eat an apple.*")
        await ctx.send(f"*Gives {user.mention} an apple.*")


def setup(bot:utils.Bot):
    x = SimulationCommands(bot)
    bot.add_cog(x)
