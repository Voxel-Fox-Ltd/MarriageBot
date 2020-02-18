import random
import asyncio
import json

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

        # Generate responses
        user_info = utils.FamilyTreeMember.get(user, ctx.family_guild_id)
        if user_info._partner == None or user_info._partner == ctx.author.id:
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

    @commands.command(aliases=['nunget', 'nuggie'])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def nugget(self, ctx:utils.Context, user:discord.Member):
        """Gives a nugget to a mentioned user"""

        if user == ctx.author:
            await ctx.send(f"*You give yourself a {ctx.invoked_with}* <:nugget:585626539605884950>")
        else:
            await ctx.send(f"*Gives {user.mention} a {ctx.invoked_with}* <:nugget:585626539605884950>")

    @commands.command(aliases=['borger', 'borg'])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def burger(self, ctx:utils.Context, user:discord.Member):
        """Gives a burger to a mentioned user"""

        if user == ctx.author:
            await ctx.send(f"*You give yourself a {ctx.invoked_with}* 🍔")
        else:
            await ctx.send(f"*Gives {user.mention} a {ctx.invoked_with}* 🍔")

    @commands.command(aliases=['dumpster'], hidden=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def garbage(self, ctx:utils.Context, user:discord.Member):
        """Throws a user in the garbage"""

        if user == ctx.author:
            await ctx.send(f"*You climb right into the trash can, where you belong*")
        else:
            await ctx.send(f"*Throws {user.mention} into the dumpster*")

    @commands.command(hidden=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def insult(self, ctx:utils.Context, user:discord.Member):
        """Sends an insult into the chat"""

        async with self.bot.session.get("https://insult.mattbas.org/api/insult.json") as r:
            text = await r.text()
        data = json.loads(text)
        await ctx.send(data['insult'])

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

    @commands.command(enabled=False)
    async def present(self, ctx:utils.Context, user:discord.Member):
        """Gives a present to the user"""

        present = random.choice([
            "Talem",
            "some candy",
            "a magnifying glass",
            "chocolate",
            "Pepsi",
            "a hairline",
            "nuggets",
            "a burger",
            "some fries",
            "potato strings",
            "a dose of happiness",
            "the feeling of love",
            "some royalty free music",
            "a free sample of milkshake",
            "a roll of wrapping paper wrapped in more wrapping paper",
            "trans rights",
            "just a theory, a game theory",
            "an envelope filled with glitter",
            "a garbage bag filled with BBQ sauce",
            "a set of lockpicks",
            "a bird mask",
            "four Tamagotchis, all neon pink",
            "a coin with two 'heads' sides",
            "a used toilet plunger",
            "a slightly damp mop",
            "a pair of unmatched socks",
            "a banana peel with a bite taken out of it",
            "a wilting mint plant",
            "dog socks",
            "a small collection of cat hairs",
            "a can of off-brand mint-flavoured cola",
            "a pack of AA batteries",
            "a Bulbasaur plushie",
            "a bad Discord bot",
            "some discontinued Discord merch",
            "chapstick",
            "a small stamp collection",
            "a soft-ass cushion",
            "an egg",
            "honey",
            "a handful of screws",
            "a toy train",
            "pain",
            "some smoke in a jar",
            "a bottle of unbranded water",
            "coal",
            "a pink collar",
            "a toy horse",
            "destruction",
            "pleasure",
            "a tin can filled with baked beans",
            "wax",
            "a skateboard",
            "bushes",
            "some Roseart crayons",
            "a jar filled with ants",
            "a rat",
            "a small vial of blood",
            "a knife",
            "power",
            "snakes",
            "cloth",
            "cheese",
            "cheesecloth",
            "liquid",
            "a snake in a box",
            "soup",
            "a yam, the worst part of Thanksgiving",
            "spiders",
            "chalk",
            "a saucy fanfiction about the bourgeoisie",
            "beef",
            "a cow in sheep's clothing",
            "silver",
            "oranges",
            "a collection of cobwebs",
            "an existential crisis",
            "string",
            "rabbits",
            "horses",
            "a lump of plastic",
            "oatmeal",
            "a raw potato",
            "toothpaste",
            "salt",
        ])
        await ctx.send(f"You give {user.mention} {present}.")

    @commands.command(aliases=['intercourse', 'fuck', 'smash', 'heck'])
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.is_nsfw()
    @utils.checks.bot_is_ready()
    async def copulate(self, ctx:utils.Context, user:discord.Member):
        """Lets you... um... heck someone"""

        # Check for the most common catches
        text_processor = utils.random_text.RandomText('copulate', ctx.author, user)
        text = text_processor.process()
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
            await ctx.send(text_processor.target_is_family())
            return

        # Ping out a message for them
        await ctx.send(text_processor.valid_target())

        # Wait for a response
        try:
            check = utils.AcceptanceCheck(user.id, ctx.channel.id).check
            m = await self.bot.wait_for('message', check=check, timeout=60.0)
            response = check(m)
        except asyncio.TimeoutError:
            return await ctx.send(text_processor.request_timeout(), ignore_error=True)

        # Process response
        if response == "NO":
            return await ctx.send(text_processor.request_denied())
        await ctx.send(text_processor.request_accepted())


def setup(bot:utils.CustomBot):
    x = Simulation(bot)
    bot.add_cog(x)
