import asyncio
import typing
import io
from datetime import datetime as dt
import voxelbotutils as utils

import discord
from discord.ext import commands

from cogs import utils as localutils


class TreeCommandCooldown(utils.cooldown.Cooldown):
    async def predicate(self, ctx):
        perks = await localutils.get_marriagebot_perks(ctx.bot, ctx.author.id)
        self.per = perks.tree_command_cooldown


class Information(utils.Cog):

    @utils.command(aliases=['spouse', 'husband', 'wife', 'marriage'])
    @utils.cooldown.no_raise_cooldown(1, 5, commands.BucketType.user)
    @utils.checks.bot_is_ready()
    @commands.bot_has_permissions(send_messages=True)
    async def partner(self, ctx:utils.Context, user:utils.converters.UserID=None):
        """
        Tells you who a user is married to.
        """

        # Get the user's info
        user_id = user or ctx.author.id
        user_name = await localutils.DiscordNameManager.fetch_name_by_id(self.bot, user_id)
        user_info = localutils.FamilyTreeMember.get(user, localutils.get_family_guild_id(ctx))

        # Check they have a partner
        if user_info._partner is None:
            if user_id == ctx.author.id:
                return await ctx.send(f"You're not currently married.", allowed_mentions=discord.AllowedMentions.none())
            return await ctx.send(
                f"**{localutils.escape_markdown(user_name)}** is not currently married.",
                allowed_mentions=discord.AllowedMentions.none(),
            )
        partner_name = await localutils.DiscordNameManager.fetch_name_by_id(self.bot, user_info._partner)

        # Get timestamp
        async with self.bot.database() as db:
            if self.bot.config.get('is_server_specific', False):
                data = await db("SELECT * FROM marriages WHERE user_id=$1 AND guild_id<>0", user)
            else:
                data = await db("SELECT * FROM marriages WHERE user_id=$1 AND guild_id=0", user)
        try:
            timestamp = data[0]['timestamp']
        except Exception:
            timestamp = None

        # Output
        text = f"**{localutils.escape_markdown(user_name)}** is currently married to **{localutils.escape_markdown(partner_name)}** (`{user_info._partner}`). "
        if user_id == ctx.author.id:
            text = f"You're currently married to **{localutils.escape_markdown(partner_name)}** (`{user_info._partner}`). "
        if timestamp:
            text += f"{'You' if user_id == ctx.author.id else 'They'}'ve been married since {timestamp.strftime('%B %d %Y')}."
        await ctx.send(text, allowed_mentions=discord.AllowedMentions.none())

    @utils.command(aliases=['child', 'kids'])
    @utils.cooldown.no_raise_cooldown(1, 5, commands.BucketType.user)
    @utils.checks.bot_is_ready()
    @commands.bot_has_permissions(send_messages=True)
    async def children(self, ctx:utils.Context, user:utils.converters.UserID=None):
        """
        Tells you who a user's children are.
        """

        # Get the user's info
        user_id = user or ctx.author.id
        user_name = await localutils.DiscordNameManager.fetch_name_by_id(self.bot, user_id)
        user_info = localutils.FamilyTreeMember.get(user_id, localutils.get_family_guild_id(ctx))

        # Get user's children
        if len(user_info._children) == 0:
            output = f"**{localutils.escape_markdown(user_name)}** has no children right now."
            if user_id == ctx.author.id:
                output = f"You have no children right now."
        else:
            output = f"**{localutils.escape_markdown(user_name)}** has {len(user_info._children)} {'child' len(user_info._children) == 1 else 'children'}:\n"
            children = [(await localutils.DiscordNameManager.fetch_name_by_id(self.bot, i), i) for i in user_info._children]
            output += "\n".join([f"* **{localutils.escape_markdown(i[0])}** (`{i[1]}`)" for i in children])

        # Return all output
        await ctx.send(output, allowed_mentions=discord.AllowedMentions.none())

    @utils.command(aliases=['parents'])
    @utils.cooldown.no_raise_cooldown(1, 5, commands.BucketType.user)
    @utils.checks.bot_is_ready()
    @commands.bot_has_permissions(send_messages=True)
    async def parent(self, ctx:utils.Context, user:utils.converters.UserID=None):
        """
        Tells you who someone's parent is.
        """

        # Get the user's info
        user_id = user or ctx.author.id
        user_name = await localutils.DiscordNameManager.fetch_name_by_id(self.bot, user_id)
        user_info = localutils.FamilyTreeMember.get(user_id, localutils.get_family_guild_id(ctx))

        # Make sure they have a parent
        if user_info._parent is None:
            if user_id == ctx.author.id:
                return await ctx.send("You have no parent.")
            return await ctx.send(f"**{localutils.escape_markdown(user_name)}** has no parent.", allowed_mentions=discord.AllowedMentions.none())
        parent_name = await localutils.DiscordNameManager.fetch_name_by_id(self.bot, user_info._parent)

        # Output parent
        output = f"**{localutils.escape_markdown(user_name)}**'s parent is **{localutils.escape_markdown(parent_name)}** (`{user_info._parent}`)."
        if user_id == ctx.author.id:
            output = f"Your parent is `{localutils.escape_markdown(parent_name)}` (`{user_info._parent}`)."
        return await ctx.send(output, allowed_mentions=discord.AllowedMentions.none())

    @utils.command(aliases=['treesize', 'fs', 'ts'])
    @utils.cooldown.no_raise_cooldown(1, 5, commands.BucketType.user)
    @utils.checks.bot_is_ready()
    @commands.bot_has_permissions(send_messages=True)
    async def familysize(self, ctx:utils.Context, user:utils.converters.UserID=None):
        """
        Gives you the size of your family tree.
        """

        # Get the user's info
        user_id = user or ctx.author.id
        user_name = await localutils.DiscordNameManager.fetch_name_by_id(self.bot, user_id)
        user_info = localutils.FamilyTreeMember.get(user_id, localutils.get_family_guild_id(ctx))

        # Get size
        async with ctx.channel.typing():
            size = user_tree.family_member_count

        # Output
        output = f"There are {size} people in **{localutils.escape_markdown(user_name)}**'s family tree."
        if user_id == ctx.author.id:
            output = f"There are {size} people in your family tree."
        return await ctx.send(output, allowed_mentions=discord.AllowedMentions.none())

    @utils.command(aliases=['relation'])
    @utils.cooldown.no_raise_cooldown(1, 5, commands.BucketType.user)
    @utils.checks.bot_is_ready()
    @commands.bot_has_permissions(send_messages=True)
    async def relationship(self, ctx:utils.Context, user:utils.converters.UserID, other:utils.converters.UserID=None):
        """
        Gets the relationship between the two specified users.
        """

        # Fix up the arguments
        if other is None:
            user_id, other_id = ctx.author.id, user
        else:
            user_id, other_id = user, other

        # See if they're the same person
        if user_id == other_id:
            if user_id == ctx.author.id:
                return await ctx.send("Unsurprisingly, you're pretty closely related to yourself.")
            return await ctx.send("Unsurprisingly, they're pretty closely related to themselves.")

        # Get their relation
        user_info, other_info = localutils.FamilyTreeMember.get_multiple(user_id, other_id, localutils.get_family_guild_id(ctx))
        async with ctx.channel.typing():
            relation = user_tree.get_relation(other_tree)

        # Get names
        user_name = await localutils.DiscordNameManager.fetch_name_by_id(self.bot, user_id)
        other_name = await localutils.DiscordNameManager.fetch_name_by_id(self.bot, other_id)

        # Output
        if relation is None:
            output = f"**{localutils.escape_markdown(user_name)}** is not related to **{localutils.escape_markdown(other_name)}**."
            if user_id == ctx.author.id:
                output = f"You're is not related to **{localutils.escape_markdown(other_name)}**."
        else:
            output = f"**{localutils.escape_markdown(other_name)}** is **{localutils.escape_markdown(user_name)}**'s {relation}."
            if user_id == ctx.author.id:
                output = f"**{localutils.escape_markdown(other_name)}** is your {relation}."
        return await ctx.send(output, allowed_mentions=discord.AllowedMentions.none())

    @utils.command(aliases=['tree', 't'])
    @utils.cooldown.cooldown(1, 60, commands.BucketType.user, cls=TreeCommandCooldown())
    @utils.checks.bot_is_ready()
    @commands.bot_has_permissions(send_messages=True, attach_files=True)
    async def familytree(self, ctx:utils.Context, user:utils.converters.UserID=None):
        """
        Gets the family tree of a given user.
        """

        try:
            return await self.treemaker(ctx=ctx, user_id=user)
        except Exception:
            raise

    @utils.command(aliases=['st', 'stupidtree'])
    @utils.cooldown.cooldown(1, 60, commands.BucketType.user, cls=TreeCommandCooldown())
    @localutils.checks.has_donator_perks("stupidtree_command")
    @utils.checks.bot_is_ready()
    @commands.bot_has_permissions(send_messages=True, attach_files=True)
    async def fulltree(self, ctx:utils.Context, user:utils.converters.UserID=None):
        """
        Gets the family tree of a given user.
        """

        try:
            return await self.treemaker(ctx=ctx, user_id=user, stupid_tree=True)
        except Exception:
            raise

    async def treemaker(self, ctx:utils.Context, user_id:int, stupid_tree:bool=False):
        """
        Handles the generation and sending of the tree to the user.
        """

        # Get their family tree
        user_id = user_id or ctx.author.id
        user_info = localutils.FamilyTreeMember.get(user_id, localutils.get_family_guild_id(ctx))
        user_name = await localutils.DiscordNameManager.fetch_name_by_id(self.bot, user_id)

        # Make sure they have one
        if tree.is_empty:
            if user_id == ctx.author.id:
                return await ctx.send(f"You have no family to put into a tree .-.")
            return await ctx.send(
                f"**{localutils.escape_markdown(user_name)}** has no family to put into a tree .-.",
                allowed_mentions=discord.AllowedMentions.none(),
            )

        # Get their customisations
        async with self.bot.database() as db:
            ctu = await localutils.CustomisedTreeUser.fetch_by_id(ctx.author.id, db)

        # Get their dot script
        async with ctx.channel.typing():
            if stupid_tree:
                dot_code = await tree.to_full_dot_script(self.bot, ctu)
            else:
                dot_code = await tree.to_dot_script(self.bot, ctu)

        # Write the dot to a file
        dot_filename = f'{self.bot.config["tree_file_location"]}/{ctx.author.id}.gz'
        try:
            with open(dot_filename, 'w', encoding='utf-8') as a:
                a.write(dot_code)
        except Exception as e:
            self.logger.error(f"Could not write to {dot_filename}")
            raise e

        # Convert to an image
        image_filename = f'{self.bot.config["tree_file_location"].rstrip("/")}/{ctx.author.id}.png',
        dot = await asyncio.create_subprocess_exec('dot', '-Tpng:gd', dot_filename, '-o', image_filename, '-Gcharset=UTF-8')
        await asyncio.wait_for(dot.wait(), 10.0, loop=self.bot.loop)

        # Kill subprocess
        try:
            dot.kill()
        except ProcessLookupError:
            pass  # It already died
        except Exception:
            raise

        # Send file
        file = discord.File(image_filename)
        text = f"[Click here](https://marriagebot.xyz/) to customise your tree."
        if not stupid_tree:
            text += f" Use `{ctx.prefix}fulltree` for your _entire_ family, including non-blood relatives."
        await ctx.send(text, file=file)

        # Delete the files
        self.bot.loop.create_task(asyncio.create_subprocess_exec('rm', dot_filename))
        self.bot.loop.create_task(asyncio.create_subprocess_exec('rm', image_filename))


def setup(bot:utils.Bot):
    x = Information(bot)
    bot.add_cog(x)
