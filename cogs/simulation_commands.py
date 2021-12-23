import random
import typing

import discord
from discord.ext import commands, vbu

from cogs import utils


class SimulationCommands(vbu.Cog):

    async def get_reaction_gif(
            self, ctx: vbu.Context, reaction_type: str = None, *, nsfw: bool = False,
            ignore_checks: bool = False) -> typing.Optional[str]:
        """
        Gets a reaction gif from the Weeb.sh API.

        Parameters
        ----------
        ctx : vbu.Context
            The context for the command.
        reaction_type : str, optional
            The type of reaction that you want to get. If not provided, then the name of the command
            in the context is used.
        nsfw : bool, optional
            Whether or not to include NSFW results.
        ignore_checks : bool, optional
            Whether or not to ignore guild checks.

        Returns
        -------
        typing.Optional[str]
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

        # Defer the interaction
        if isinstance(ctx, commands.SlashContext):
            await ctx.interaction.response.defer()

        # If we can't return images, then don't
        elif ctx.guild and not ctx.channel.permissions_for(ctx.guild.me).embed_links:
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
        async with self.bot.session.get("https://api.weeb.sh/images/random", params=params, headers=headers) as r:
            try:
                data = await r.json()
            except Exception as e:
                data = await r.text()
                self.logger.warning(f"Error from Weeb.sh ({e}): {str(data)}")
                return None
            if r.ok:
                return data['url']
        return None

    @commands.command(aliases=['snuggle', 'cuddle'])
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def hug(self, ctx: vbu.Context, user: discord.Member):
        """
        Hugs a mentioned user.
        """

        if user == ctx.author:
            return await ctx.send("*You hug yourself... and start crying.*")
        image_url = await self.get_reaction_gif(ctx)
        await vbu.embeddify(ctx, f"*Hugs {user.mention}.*", image_url=image_url)

    @commands.command(aliases=['smooch', 'makeout'])
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def kiss(self, ctx: vbu.Context, user: discord.Member):
        """
        Kisses a mentioned user.
        """

        if user == ctx.author:
            return await ctx.send("How would you even manage to do that?")
        image_url = await self.get_reaction_gif(ctx)
        await vbu.embeddify(ctx, f"*Kisses {user.mention}.*", image_url=image_url)

    @commands.command(aliases=['smack'])
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def slap(self, ctx: vbu.Context, user: discord.Member):
        """
        Slaps a mentioned user.
        """

        if user == ctx.author:
            return await ctx.send("*You slapped yourself... for some reason.*")
        image_url = await self.get_reaction_gif(ctx)
        await vbu.embeddify(ctx, f"*Slaps {user.mention}.*", image_url=image_url)

    @commands.command(hidden=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def coffee(self, ctx: vbu.Context, user: discord.Member = None):
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

    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def punch(self, ctx: vbu.Context, user: discord.Member):
        """
        Punches a mentioned user.
        """

        if user == ctx.author:
            return await ctx.send("*You punched yourself... for some reason.*")
        image_url = await self.get_reaction_gif(ctx)
        await vbu.embeddify(ctx, f"*Punches {user.mention} right in the nose.*", image_url=image_url)

    @commands.command(hidden=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def cookie(self, ctx: vbu.Context, user: discord.Member):
        """
        Gives a cookie to a mentioned user.
        """

        if user == ctx.author:
            return await ctx.send("*You gave yourself a cookie.*")
        await ctx.send(f"*Gives {user.mention} a cookie.*")

    @commands.command(aliases=['nunget', 'nuggie'], hidden=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True, use_external_emojis=True)
    async def nugget(self, ctx: vbu.Context, user: discord.Member):
        """
        Gives a nugget to a mentioned user.
        """

        if user == ctx.author:
            return await ctx.send(f"*You give yourself a {ctx.invoked_with}* <:nugget:585626539605884950>")
        await ctx.send(f"*Gives {user.mention} a {ctx.invoked_with}* <:nugget:585626539605884950>")

    @commands.command(aliases=['borger', 'borg'], hidden=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def burger(self, ctx: vbu.Context, user: discord.Member):
        """
        Gives a burger to a mentioned user.
        """

        if user == ctx.author:
            return await ctx.send(f"*You give yourself a {ctx.invoked_with}* 🍔")
        await ctx.send(f"*Gives {user.mention} a {ctx.invoked_with}* 🍔")

    @commands.command(hidden=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def tea(self, ctx: vbu.Context, user: discord.Member):
        """
        Gives tea to a mentioned user.
        """

        if user == ctx.author:
            return await ctx.send("*You gave yourself tea.*")
        await ctx.send(f"*Gives {user.mention} tea.*")

    @commands.command(aliases=['dumpster'], hidden=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def garbage(self, ctx: vbu.Context, user: discord.Member):
        """
        Throws a user in the garbage.
        """

        if user == ctx.author:
            return await ctx.send("*You climb right into the trash can, where you belong.*")
        await ctx.send(f"*Throws {user.mention} into the dumpster.*")

    @commands.command(hidden=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def fistbump(self, ctx: vbu.Context, user: discord.Member):
        """
        Give a fistbump to another user.
        """

        if user == ctx.author:
            return await ctx.send("\N{CLAPPING HANDS SIGN}")
        await ctx.send(f"*You missed and hit {user.mention} in the face.*")

    @commands.command(hidden=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def bonk(self, ctx: vbu.Context, user: discord.Member):
        """
        Bonk.
        """

        return await ctx.send("*Bonk*")

    @commands.command(aliases=['pat', 'pet'], hidden=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def headpat(self, ctx: vbu.Context, user: discord.Member):
        """
        Give a fistbump to another user.
        """

        if user == ctx.author:
            return await ctx.send("*You pat yourself on the head. This is fine. Everything is normal.*")
        await ctx.send(f"*You gently pet {user.mention} on the head :3*")

    @commands.command(aliases=['waterbaloon', 'waterballon', 'waterbalon', 'waterblon'], hidden=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def waterballoon(self, ctx: vbu.Context, user: discord.Member):
        """
        Throw a waterballoon at another user.
        """

        if user == ctx.author:
            return await ctx.send("*You calmly look at a water balloon for a few moments before smashing it into your own face.*")
        await ctx.send(f"*You throw a water balloon at {user.mention}, soaking them.*")

    @commands.command(hidden=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def poke(self, ctx: vbu.Context, user: discord.Member):
        """
        Pokes a given user.
        """

        if user == ctx.author:
            return await ctx.send("You poke yourself.")
        image_url = await self.get_reaction_gif(ctx)
        await vbu.embeddify(ctx, f"*Pokes {user.mention}.*", image_url=image_url)

    @commands.command(hidden=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def stab(self, ctx: vbu.Context, user: discord.Member):
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

    @commands.command(aliases=['murder'], hidden=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def kill(self, ctx: vbu.Context, user: discord.Member = None):
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

    @commands.command(aliases=['vore'], hidden=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def eat(self, ctx: vbu.Context, user: discord.Member):
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

    @commands.command(hidden=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def sleep(self, ctx: vbu.Context):
        """
        Todd Howard strikes once more.
        """

        await ctx.send((
            "You sleep for a while and when you wake up you're in a cart "
            "with your hands bound. A man says \"Hey, you. You're finally "
            "awake. You were trying to cross the border, right?\""
        ))

    @commands.command(hidden=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def chocolate(self, ctx: vbu.Context, user: discord.Member):
        """
        Gives chocolate to a mentioned user.
        """

        if user == ctx.author:
            return await ctx.send("*You bought some choclate.*")
        await ctx.send(f"*Gives {user.mention} chocolate.*")

    @commands.command(hidden=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def wave(self, ctx: vbu.Context, user: discord.Member = None):
        """
        Waves to someone
        """

        if user is None or user == ctx.author:
            return await ctx.send("*You wave to yourself... consider getting some friends.*")
        await ctx.send(f"*Waves to {user.mention} :wave:")

    @commands.command(hidden=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def apple(self, ctx: vbu.Context, user: discord.Member):
        """
        Gives a apple to a mentioned user.
        """

        if user == ctx.author:
            return await ctx.send("*You eat an apple.*")
        await ctx.send(f"*Gives {user.mention} an apple.*")

    @commands.command(hidden=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def dance(self, ctx: vbu.Context, user: discord.Member):
        """
        you are the dancing queen.
        """

        if user == ctx.author:
            return await ctx.send("You uhm.. dance.. with yourself.")
        await ctx.send(f"*You dance with {user.mention}!*")

    @commands.command(hidden=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def pancakes(self, ctx: vbu.Context, user: discord.Member):
        """
        Pancakes. Don't know what else to tell you.
        """

        if user == ctx.author:
            return await ctx.send("You make pancakes... and eat them.")
        await ctx.send(f"*You make panckaes for {user.mention}.*")

    @commands.command(hidden=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def tissue(self, ctx: vbu.Context, user: discord.Member):
        """
        GIve a tissue to one of your friends.
        """

        if user == ctx.author:
            return await ctx.send("*You bury your face in a tissue.*")
        await ctx.send(f"*You gently wipe away tears from {user.mention}'s face.*")

    @commands.command(hidden=True, aliases=['crepes'])
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def crepe(self, ctx: vbu.Context, user: discord.Member):
        """
        Crepes. Don't know what else to tell you.
        """

        if user == ctx.author:
            return await ctx.send("You make crepes... and eat them.")
        await ctx.send(f"*You make crepes for {user.mention}. Delicious.*")

    @commands.command()
    @commands.bot_has_permissions(send_messages=True)
    async def ship(self, ctx: vbu.Context, user: discord.Member, user2: discord.Member = None):
        """
        Gives you a ship percentage between two users.
        """

        # Fix attrs
        if user2 is None:
            user, user2 = ctx.author, user  # type: ignore

        # Add response for yourself
        if user == user2:
            return await ctx.send("-.-")

        # Get percentage
        async with vbu.Database() as db:
            rows = await db(
                "SELECT * FROM ship_percentages WHERE user_id_1=ANY($1::BIGINT[]) AND user_id_2=ANY($1::BIGINT[])",
                [user.id, user2.id],
            )
        if rows and rows[0]['percentage']:
            percentage = rows[0]['percentage'] / 100
        else:
            percentage = ((user.id + user2.id + 4500) % 10001) / 100
        return await ctx.send(
            (
                f"{user.mention} \N{REVOLVING HEARTS} **{percentage:.2f}%** "
                f"\N{REVOLVING HEARTS} {user2.mention}"
            ),
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @commands.command(aliases=['compat'], hidden=True)
    @commands.bot_has_permissions(send_messages=True)
    async def comatibility(self, ctx: vbu.Context, user: discord.Member, user2: discord.Member = None):
        """
        Tells you how compatible two users may or may not be.
        """

        # Fix attrs
        if user2 is None:
            user, user2 = ctx.author, user  # type: ignore

        # Add response for yourself
        if user == user2:
            return await ctx.send("-.-")

        percentage = random.randint(0, 10_000) / 100
        return await ctx.send(
            (
                f"{user.mention} \N{REVOLVING HEARTS} **{percentage:.2f}%** "
                f"\N{REVOLVING HEARTS} {user2.mention}"
            ),
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @commands.command(aliases=['intercourse', 'fuck', 'smash', 'heck', 'sex'], hidden=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.is_nsfw()
    @vbu.checks.bot_is_ready()
    @commands.bot_has_permissions(send_messages=True)
    async def copulate(self, ctx: vbu.Context, target: discord.Member):
        """
        Lets you... um... heck someone.
        """

        # Variables we're gonna need for later
        family_guild_id = utils.get_family_guild_id(ctx)
        author_tree, target_tree = utils.FamilyTreeMember.get_multiple(ctx.author.id, target.id, guild_id=family_guild_id)

        # Check they're not a bot
        if target.id == self.bot.user.id:
            return await ctx.send("Ew. No. Thanks.")
        if target.id == ctx.author.id:
            return

        # See if they're already related
        async with ctx.typing():
            relation = author_tree.get_relation(target_tree)
        if relation and relation != "partner" and utils.guild_allows_incest(ctx) is False:
            return await ctx.send(
                f"Woah woah woah, it looks like you guys are related! {target.mention} is your {relation}!",
                allowed_mentions=utils.only_mention(ctx.author),
            )

        # Set up the proposal
        result = None
        if target.id != ctx.author.id:
            try:
                result = await utils.send_proposal_message(
                    ctx, target,
                    f"Hey, {target.mention}, {ctx.author.mention} do you wanna... smash? \N{SMIRKING FACE}",
                    allow_bots=True,
                )
            except Exception:
                result = None
        if result is None:
            return

        # Respond
        if isinstance(result.ctx, commands.SlashContext):
            sendable = result.ctx.followup
        else:
            sendable = result.ctx
        await sendable.send(
            random.choice(utils.random_text.Copulate.VALID).format(author=ctx.author, target=target),
        )


def setup(bot: vbu.Bot):
    x = SimulationCommands(bot)
    bot.add_cog(x)
