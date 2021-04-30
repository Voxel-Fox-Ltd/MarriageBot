import random
import asyncio
import typing

import discord
from discord.ext import commands
import voxelbotutils as utils

from cogs import utils as localutils


class SimulationCommands(utils.Cog):

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
            "type": reaction_type or ctx.command.name,
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
    @utils.cooldown.no_raise_cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def hug(self, ctx:utils.Context, user:discord.Member):
        """
        Hugs a mentioned user.
        """

        if user == ctx.author:
            return await ctx.send("*You hug yourself... and start crying.*")
        image_url = await self.get_reaction_gif(ctx)
        await ctx.send(f"*Hugs {user.mention}.*", image_url=image_url)

    @utils.command(aliases=['smooch', 'makeout'])
    @utils.cooldown.no_raise_cooldown(1, 3, commands.BucketType.user)
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
    @utils.cooldown.no_raise_cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def slap(self, ctx:utils.Context, user:discord.Member):
        """
        Slaps a mentioned user.
        """

        if user == ctx.author:
            return await ctx.send("*You slapped yourself... for some reason.*")
        image_url = await self.get_reaction_gif(ctx)
        await ctx.send(f"*Slaps {user.mention}.*", image_url=image_url)

    @utils.command(hidden=True)
    @utils.cooldown.no_raise_cooldown(1, 3, commands.BucketType.user)
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
    @utils.cooldown.no_raise_cooldown(1, 3, commands.BucketType.user)
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
    @utils.cooldown.no_raise_cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def cookie(self, ctx:utils.Context, user:discord.Member):
        """
        Gives a cookie to a mentioned user.
        """

        if user == ctx.author:
            return await ctx.send("*You gave yourself a cookie.*")
        await ctx.send(f"*Gives {user.mention} a cookie.*")

    @utils.command(aliases=['nunget', 'nuggie'], hidden=True)
    @utils.cooldown.no_raise_cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True, use_external_emojis=True)
    async def nugget(self, ctx:utils.Context, user:discord.Member):
        """
        Gives a nugget to a mentioned user.
        """

        if user == ctx.author:
            return await ctx.send(f"*You give yourself a {ctx.invoked_with}* <:nugget:585626539605884950>")
        await ctx.send(f"*Gives {user.mention} a {ctx.invoked_with}* <:nugget:585626539605884950>")

    @utils.command(aliases=['borger', 'borg'], hidden=True)
    @utils.cooldown.no_raise_cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def burger(self, ctx:utils.Context, user:discord.Member):
        """
        Gives a burger to a mentioned user.
        """

        if user == ctx.author:
            return await ctx.send(f"*You give yourself a {ctx.invoked_with}* 🍔")
        await ctx.send(f"*Gives {user.mention} a {ctx.invoked_with}* 🍔")

    @utils.command(hidden=True)
    @utils.cooldown.no_raise_cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def tea(self, ctx:utils.Context, user:discord.Member):
        """
        Gives tea to a mentioned user.
        """

        if user == ctx.author:
            return await ctx.send("*You gave yourself tea.*")
        await ctx.send(f"*Gives {user.mention} tea.*")

    @utils.command(aliases=['dumpster'], hidden=True)
    @utils.cooldown.no_raise_cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def garbage(self, ctx:utils.Context, user:discord.Member):
        """
        Throws a user in the garbage.
        """

        if user == ctx.author:
            return await ctx.send("*You climb right into the trash can, where you belong.*")
        await ctx.send(f"*Throws {user.mention} into the dumpster.*")

    @utils.command(hidden=True)
    @utils.cooldown.no_raise_cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def fistbump(self, ctx:utils.Context, user:discord.Member):
        """
        Give a fistbump to another user.
        """

        if user == ctx.author:
            return await ctx.send("\N{CLAPPING HANDS SIGN}")
        await ctx.send(f"*You missed and hit {user.mention} in the face.*")

    @utils.command(hidden=True)
    @utils.cooldown.no_raise_cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def bonk(self, ctx:utils.Context, user:discord.Member):
        """
        Bonk.
        """

        return await ctx.send("*Bonk*")

    @utils.command(aliases=['pat', 'pet'], hidden=True)
    @utils.cooldown.no_raise_cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def headpat(self, ctx:utils.Context, user:discord.Member):
        """
        Give a fistbump to another user.
        """

        if user == ctx.author:
            return await ctx.send("*You pat yourself on the head. This is fine. Everything is normal.*")
        # image_url = await self.get_reaction_gif(ctx, reaction_type="pat")
        # await ctx.send(f"*Pets {user.mention}.*", image_url=image_url)
        await ctx.send(f"*You gently pet {user.mention} on the head :3*")

    @utils.command(aliases=['waterbaloon', 'waterballon', 'waterbalon', 'waterblon'], hidden=True)
    @utils.cooldown.no_raise_cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def waterballoon(self, ctx:utils.Context, user:discord.Member):
        """
        Throw a waterballoon at another user.
        """

        if user == ctx.author:
            return await ctx.send("*You calmly look at a water balloon for a few moments before smashing it into your own face.*")
        await ctx.send(f"*You throw a water balloon at {user.mention}, soaking them.*")

    @utils.command(hidden=True)
    @utils.cooldown.no_raise_cooldown(1, 3, commands.BucketType.user)
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
    @utils.cooldown.no_raise_cooldown(1, 3, commands.BucketType.user)
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
    @utils.cooldown.no_raise_cooldown(1, 3, commands.BucketType.user)
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
    @utils.cooldown.no_raise_cooldown(1, 3, commands.BucketType.user)
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
    @utils.cooldown.no_raise_cooldown(1, 3, commands.BucketType.user)
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

    @utils.command(hidden=True)
    @utils.cooldown.no_raise_cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def chocolate(self, ctx:utils.Context, user:discord.Member):
        """
        Gives chocolate to a mentioned user.
        """

        if user == ctx.author:
            return await ctx.send("*You bought some choclate.*")
        await ctx.send(f"*Gives {user.mention} chocolate.*")

    @utils.command(hidden=True)
    @utils.cooldown.no_raise_cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def wave(self, ctx:utils.Context, user:discord.Member=None):
        """
        Waves to someone
        """

        if user is None or user == ctx.author:
            return await ctx.send("*You wave to yourself... consider getting some friends.*")
        await ctx.send(f"*Waves to {user.mention} :wave:")

    @utils.command(hidden=True)
    @utils.cooldown.no_raise_cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def apple(self, ctx:utils.Context, user:discord.Member):
        """
        Gives a apple to a mentioned user.
        """

        if user == ctx.author:
            return await ctx.send("*You eat an apple.*")
        await ctx.send(f"*Gives {user.mention} an apple.*")

    @utils.command(hidden=True)
    @utils.cooldown.no_raise_cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def dance(self, ctx:utils.Context, user:discord.Member):
        """
        you are the dancing queen.
        """

        if user == ctx.author:
            return await ctx.send("You uhm.. dance.. with yourself.")
        await ctx.send(f"*You dance with {user.mention}!*")

    @utils.command(hidden=True)
    @utils.cooldown.no_raise_cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def pancakes(self, ctx:utils.Context, user:discord.Member):
        """
        Pancakes. Don't know what else to tell you.
        """

        if user == ctx.author:
            return await ctx.send("You make pancakes... and eat them.")
        await ctx.send(f"*You make panckaes for {user.mention}.*")

    @utils.command()
    @commands.bot_has_permissions(send_messages=True)
    async def ship(self, ctx:utils.Context, user:discord.Member, user2:discord.Member=None):
        """
        Gives you a ship percentage between two users.
        """

        # Fix attrs
        if user2 is None:
            user, user2 = ctx.author, user

        # Add response for yourself
        if user == user2:
            return await ctx.send("-.-")

        # Get percentage
        async with self.bot.database() as db:
            rows = await db("SELECT * FROM ship_percentages WHERE user_id_1=ANY($1::BIGINT[]) AND user_id_2=ANY($1::BIGINT[])", [user.id, user2.id])
        if rows and rows[0]['percentage']:
            percentage = rows[0]['percentage'] / 100
        else:
            percentage = ((user.id + user2.id + 4500) % 10001) / 100
        return await ctx.send(f"{user.mention} \N{REVOLVING HEARTS} **{percentage:.2f}%** \N{REVOLVING HEARTS} {user2.mention}", allowed_mentions=discord.AllowedMentions(users=False))

    @utils.command(aliases=['compat'], hidden=True)
    @commands.bot_has_permissions(send_messages=True)
    async def comatibility(self, ctx:utils.Context, user:discord.Member, user2:discord.Member=None):
        """
        Tells you how compatible two users may or may not be.
        """

        # Fix attrs
        if user2 is None:
            user, user2 = ctx.author, user

        # Add response for yourself
        if user == user2:
            return await ctx.send("-.-")

        percentage = random.randint(0, 10_000) / 100
        return await ctx.send(f"{user.mention} \N{REVOLVING HEARTS} **{percentage:.2f}%** \N{REVOLVING HEARTS} {user2.mention}", allowed_mentions=discord.AllowedMentions(users=False))

    @utils.command(aliases=['intercourse', 'fuck', 'smash', 'heck', 'sex'], hidden=True)
    @utils.cooldown.no_raise_cooldown(1, 3, commands.BucketType.user)
    @commands.is_nsfw()
    @utils.checks.bot_is_ready()
    @commands.bot_has_permissions(send_messages=True)
    async def copulate(self, ctx:utils.Context, target:discord.Member):
        """
        Lets you... um... heck someone.
        """

        # Variables we're gonna need for later
        family_guild_id = localutils.get_family_guild_id(ctx)
        author_tree, target_tree = localutils.FamilyTreeMember.get_multiple(ctx.author.id, target.id, guild_id=family_guild_id)

        # Check they're not a bot
        if target.id == self.bot.user.id:
            return await ctx.send("Ew. No. Thanks.")

        # See if they're already related
        async with ctx.channel.typing():
            relation = author_tree.get_relation(target_tree)
        if relation and relation != "partner" and localutils.guild_allows_incest(ctx) is False:
            return await ctx.send(
                f"Woah woah woah, it looks like you guys are related! {target.mention} is your {relation}!",
                allowed_mentions=localutils.only_mention(ctx.author),
            )

        # Set up the proposal
        if target.id != ctx.author.id:
            try:
                result = await localutils.send_proposal_message(
                    ctx, target,
                    f"Hey, {target.mention}, {ctx.author.mention} do you wanna... smash? \N{SMIRKING FACE}",
                    allow_bots=True,
                )
            except Exception:
                result = None
            if result is None:
                return

        # Respond
        await result.ctx.send(random.choice(localutils.random_text.Copulate.VALID).format(author=ctx.author, target=target))


def setup(bot:utils.Bot):
    x = SimulationCommands(bot)
    bot.add_cog(x)
