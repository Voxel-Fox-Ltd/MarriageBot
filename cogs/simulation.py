import random
import asyncio

import discord
from discord.ext import commands

from cogs import utils


class Simulation(utils.Cog):
    """A class to handle the simulation commands inside of the bot"""

    @commands.command(aliases=['snuggle', 'cuddle'])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def hug(self, ctx:utils.Context, user:discord.Member):
        """Hugs a mentioned user"""

        if user == ctx.author:
            await ctx.send(f"*You hug yourself... and start crying.*")
        else:
            await ctx.send(f"*Hugs {user.mention}*")

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @utils.checks.bot_is_ready()
    async def kiss(self, ctx:utils.Context, user:discord.Member):
        """Kisses a mentioned user"""

        # Check if they're themself
        if user == ctx.author:
            await ctx.send(f"How would you even manage to do that?")
            return

        # Check if they're related
        x = utils.FamilyTreeMember.get(ctx.author.id)
        y = utils.FamilyTreeMember.get(user.id)
        async with ctx.channel.typing():
            relationship = x.get_relation(y)

        # Generate responses
        if relationship == None or relationship.casefold() == 'partner':
            responses = [
                f"*Kisses {user.mention}*"
            ]
        else:
            responses = [
                f"Woah woah, you two are family!",
                f"Incest is wincest, I guess.",
                f"You two are related but go off I guess.",
            ]

        # Boop an output
        await ctx.send(random.choice(responses))

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def slap(self, ctx:utils.Context, user:discord.Member):
        """Slaps a mentioned user"""

        if user == ctx.author:
            await ctx.send(f"*You slapped yourself... for some reason.*")
        else:
            await ctx.send(f"*Slaps {user.mention}*")

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def punch(self, ctx:utils.Context, user:discord.Member):
        """Punches a mentioned user"""

        if user == ctx.author:
            await ctx.send("*You punched yourself... for some reason.*")
        else:
            await ctx.send(f"*Punches {user.mention} right in the nose*")

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def cookie(self, ctx:utils.Context, user:discord.Member):
        """Gives a cookie to a mentioned user"""

        if user == ctx.author:
            await ctx.send("*You gave yourself a cookie.*")
        else:
            await ctx.send(f"*Gives {user.mention} a cookie*")

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def poke(self, ctx:utils.Context, user:discord.Member):
        """Pokes a given user"""

        if user == ctx.author:
            await ctx.send("You poke yourself.")
        else:
            await ctx.send(f"*Pokes {user.mention}.*")

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def stab(self, ctx:utils.Context, user:discord.Member):
        """Stabs a mentioned user"""

        if user == ctx.author:
            responses = [
                f"You stab yourself.",
                f"Looks like you don't have a knife, oops!",
                f"No.",
            ]
        else:
            responses = [
                f"You stab {user.mention}.",
                f"{user.mention} has been stabbed.",
                f"*stabs {user.mention}.*",
                f"Looks like you don't have a knife, oops!",
                "You can't legally stab someone without thier consent.",
                "Stab? Isn't that, like, illegal?",
                "I wouldn't recommend doing that tbh.",
            ]
        await ctx.send(random.choice(responses))

    @commands.command(hidden=True, aliases=['murder'])
    async def kill(self, ctx:utils.Context, user:discord.Member=None):
        """Kills a person :/"""

        responses = [
            "That would violate at least one of the laws of robotics.",
            "I am a text-based bot. I cannot kill.",
            "Unfortunately, murder isn't supported in this version of MarriageBot.",
            "Haha good joke there, but I'd never kill a person! >.>",
            "To my knowledge, you can't kill via the internet. Let me know when that changes.",
            "I am designed to bring people together, not murder them.",
        ]
        await ctx.send(random.choice(responses))

    @commands.command(aliases=['vore'], hidden=True)
    async def eat(self, ctx:utils.Context, user:discord.Member=None):
        """Eats a person OwO"""

        responses = [
            f"You swallowed {user.mention}... through the wrong hole.",
            f"You've eaten {user.mention}. Gross.",
            f"Are you into this or something? You've eaten {user.mention}.",
            f"I guess lunch wasnt good enough. You eat {user.mention}.",
            f"You insert {user.mention} into your mouth and proceed to digest them.",
        ]
        await ctx.send(random.choice(responses))

    @commands.command(hidden=True)
    async def sleep(self, ctx:utils.Context):
        """Todd Howard strikes once more"""

        await ctx.send("You sleep for a while and when you wake up you're in a cart "
                       "with your hands bound. A man says \"Hey, you. You're finally "
                       "awake. You were trying to cross the border, right?\"")

    @commands.command(aliases=['intercourse', 'fuck', 'smash'])
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.is_nsfw()
    @utils.checks.bot_is_ready()
    async def copulate(self, ctx:utils.Context, user:discord.Member):
        """Let's you... um... heck someone"""

        # Check for the most common catches
        text_processor = utils.random_text.CopulateRandomText(self.bot)
        text = text_processor.process(ctx.author, user)
        if text:
            return await ctx.send(text)

        # Check if they are related
        x = utils.FamilyTreeMember.get(ctx.author.id)
        y = utils.FamilyTreeMember.get(user.id)
        async with ctx.channel.typing():
            relationship = x.get_relation(y)
        if relationship == None or relationship.casefold() == 'partner':
            pass
        elif not self.bot.allows_incest(ctx.guild.id):
            pass
        else:
            await ctx.send(text_processor.target_is_relation(ctx.author, user))
            return

        # Ping out a message for them
        await ctx.send(text_processor.valid_target(ctx.author, user))

        # Wait for a response
        try:
            check = utils.AcceptanceCheck(user.id, ctx.channel.id).check
            m = await self.bot.wait_for('message', check=check, timeout=60.0)
            response = check(m)
        except asyncio.TimeoutError:
            return await ctx.send(text_processor.proposal_timed_out(ctx.author, user), ignore_error=True)

        # Process response
        if response == "NO":
            return await ctx.send(text_processor.request_denied(ctx.author, user))
        await ctx.send(text_processor.request_accepted(ctx.author, user))


def setup(bot:utils.CustomBot):
    x = Simulation(bot)
    bot.add_cog(x)
