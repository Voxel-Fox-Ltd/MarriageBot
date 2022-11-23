from __future__ import annotations

from typing import Optional
import asyncio
import collections
from uuid import uuid4

import discord
from discord.ext import commands, vbu

from cogs import utils



class TreeCommandCooldown(object):

    bot: Optional[utils.types.Bot] = None

    @classmethod
    def cooldown(cls, _: discord.Message) -> commands.Cooldown:
        assert cls.bot
        # perks: utils.MarriageBotPerks
        # perks = cls.bot.loop.(utils.get_marriagebot_perks(cls.bot, message.author.id))
        # return commands.Cooldown(1, perks.tree_command_cooldown)
        return commands.Cooldown(1, 15)


class Information(vbu.Cog[utils.types.Bot]):

    def __init__(self, bot):
        super().__init__(bot)
        TreeCommandCooldown.bot = bot
        self.locks = collections.defaultdict(asyncio.Lock)

    def get_lock(self, user_id: int) -> asyncio.Lock:
        """
        Gets the lock for a particular user.
        """

        return self.locks[user_id]

    @commands.command(
        aliases=["spouse", "husband", "wife", "marriage", "partner"],
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="user",
                    description="The user who you want to check the partner of.",
                    type=discord.ApplicationCommandOptionType.user,
                    required=False,
                ),
            ],
        ),
    )
    @commands.defer()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @vbu.checks.bot_is_ready()
    @commands.bot_has_permissions(send_messages=True)
    async def partners(
            self,
            ctx: vbu.Context,
            user: Optional[vbu.converters.UserID] = None):
        """
        Tells you who a user is married to.
        """

        # Get the user's info
        user_id = user or ctx.author.id
        user_name = await utils.DiscordNameManager.fetch_name_by_id(self.bot, user_id)
        guild_id = utils.get_family_guild_id(ctx)
        user_info = utils.FamilyTreeMember.get(user_id, guild_id)

        # Check they have a partner
        partners = list(user_info.partners)
        if not partners:
            if user_id == ctx.author.id:
                return await ctx.send(
                    "You're not currently married.",
                    allowed_mentions=discord.AllowedMentions.none(),
                )
            return await ctx.send(
                f"**{utils.escape_markdown(user_name)}** is not currently married.",
                allowed_mentions=discord.AllowedMentions.none(),
            )

        # Work out the partner names
        partner_names = []
        for p in partners:
            name = await utils.DiscordNameManager.fetch_name_by_id(
                self.bot,
                p.id,
            )
            partner_names.append(name)
        escaped_partner_names = [
            f"**{utils.escape_markdown(i)}**"
            for i in partner_names
        ]

        # And output
        text = vbu.format(
            (
                "{0:pronoun,You are,**{1}** is} currently married to "
                "{2:humanjoin}."
            ),
            user_id == ctx.author.id, user_name, escaped_partner_names
        )
        await vbu.embeddify(
            ctx,
            text,
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @commands.command(
        aliases=["child", "kids"],
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="user",
                    description="The user who you want to check the children of.",
                    type=discord.ApplicationCommandOptionType.user,
                    required=False,
                ),
            ],
        ),
    )
    @commands.defer()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @vbu.checks.bot_is_ready()
    @commands.bot_has_permissions(send_messages=True)
    async def children(
            self,
            ctx: vbu.Context,
            user: Optional[vbu.converters.UserID] = None):
        """
        Tells you who a user's children are.
        """

        # Get the user's info
        user_id = user or ctx.author.id
        user_name = await utils.DiscordNameManager.fetch_name_by_id(self.bot, user_id)
        guild_id = utils.get_family_guild_id(ctx)
        user_info = utils.FamilyTreeMember.get(user_id, guild_id)

        # See if the user has no children
        if len(user_info._children) == 0:
            if user_id == ctx.author.id:
                return await ctx.send(
                    "You have no children right now.",
                    allowed_mentions=discord.AllowedMentions.none(),
                )
            return await ctx.send(
                f"**{utils.escape_markdown(user_name)}** has no children right now.",
                allowed_mentions=discord.AllowedMentions.none(),
            )

        # They do have children!
        children_plural = "child" if len(user_info._children) == 1 else "children"
        output = (
            f"**{utils.escape_markdown(user_name)}** has "
            f"{len(user_info._children)} {children_plural}:\n"
        )
        if user_id == ctx.author.id:
            output = f"You have {len(user_info._children)} {children_plural}:\n"
        children = [
            (await utils.DiscordNameManager.fetch_name_by_id(self.bot, i), i,)
            for i in user_info._children
        ]
        output += "\n".join([
            f"\N{BULLET} **{utils.escape_markdown(i[0])}** (`{i[1]}`)"
            for i in children
        ])

        # Return all output
        if len(output) > 2_000:
            return await ctx.send(f"<@{user_id}>'s children list goes over 2,000 characters. Amazing.")
        await vbu.embeddify(ctx, output, allowed_mentions=discord.AllowedMentions.none())

    @commands.command(
        aliases=["sib", "brothers", "sisters"],
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="user",
                    description="The user who you want to check the siblings of.",
                    type=discord.ApplicationCommandOptionType.user,
                    required=False,
                ),
            ],
        ),
    )
    @commands.defer()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @vbu.checks.bot_is_ready()
    @commands.bot_has_permissions(send_messages=True)
    async def siblings(
            self,
            ctx: vbu.Context,
            user: Optional[vbu.converters.UserID] = None):
        """
        Tells you who a user's siblings are.
        """

        # Get the user's info
        user_id = user or ctx.author.id
        user_name = await utils.DiscordNameManager.fetch_name_by_id(self.bot, user_id)
        guild_id = utils.get_family_guild_id(ctx)
        user_info = utils.FamilyTreeMember.get(user_id, guild_id)

        # Make sure they have a parent
        parent_id = user_info._parent
        if not parent_id:
            if user_id == ctx.author.id:
                return await ctx.send(
                    "You have no siblings.",
                    allowed_mentions=discord.AllowedMentions.none(),
                )
            return await ctx.send(
                f"**{utils.escape_markdown(user_name)}** has no siblings.",
                allowed_mentions=discord.AllowedMentions.none(),
            )

        # Get parent's children
        parent_info = user_info.parent
        assert parent_info
        sibling_list = parent_info.children

        # Remove the user from the sibling list
        sibling_list = [sibling for sibling in sibling_list if sibling != user_id]

        # If the user has no siblings
        if not sibling_list:
            if user_id == ctx.author.id:
                return await ctx.send(
                    "You have no siblings right now.",
                    allowed_mentions=discord.AllowedMentions.none(),
                )
            return await ctx.send(
                f"**{utils.escape_markdown(user_name)}** has no siblings right now.",
                allowed_mentions=discord.AllowedMentions.none(),
            )

        # They do have siblings!
        sibling_plural = "sibling" if len(sibling_list) == 1 else "siblings"

        # Count the siblings
        output = f"**{utils.escape_markdown(user_name)}** has {len(sibling_list)} {sibling_plural}:\n"
        if user_id == ctx.author.id:
            output = f"You have {len(sibling_list)} {sibling_plural}:\n"

        # Get the name of the siblings
        sibling_list = [
            (await utils.DiscordNameManager.fetch_name_by_id(self.bot, sibling.id), sibling,)
            for sibling in sibling_list
        ]
        output += "\n".join([
            f"\N{BULLET} **{utils.escape_markdown(username)}** (`{uid}`)"
            for username, uid in sibling_list
        ])

        # Return all output
        if len(output) > 2_000:
            return await ctx.send((
                f"**{utils.escape_markdown(user_name)}**'s sibling list goes "
                "over 2,000 characters. Amazing."
            ))
        await vbu.embeddify(ctx, output, allowed_mentions=discord.AllowedMentions.none())

    @commands.command(
        aliases=["parents"],
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="user",
                    description="The user who you want to check the parent of.",
                    type=discord.ApplicationCommandOptionType.user,
                    required=False,
                ),
            ],
        ),
    )
    @commands.defer()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @vbu.checks.bot_is_ready()
    @commands.bot_has_permissions(send_messages=True)
    async def parent(
            self,
            ctx: vbu.Context,
            user: Optional[vbu.converters.UserID] = None):
        """
        Tells you who someone's parent is.
        """

        # Get the user's info
        user_id = user or ctx.author.id
        user_name = await utils.DiscordNameManager.fetch_name_by_id(self.bot, user_id)
        guild_id = utils.get_family_guild_id(ctx)
        user_info = utils.FamilyTreeMember.get(user_id, guild_id)

        # Make sure they have a parent
        if user_info._parent is None:
            if user_id == ctx.author.id:
                return await ctx.send(
                    "You have no parent.",
                    allowed_mentions=discord.AllowedMentions.none(),
                )
            return await ctx.send(
                f"**{utils.escape_markdown(user_name)}** has no parent.",
                allowed_mentions=discord.AllowedMentions.none(),
            )
        parent_name = await utils.DiscordNameManager.fetch_name_by_id(self.bot, user_info._parent)

        # Output parent
        output = (
            f"**{utils.escape_markdown(user_name)}**'s parent "
            f"is **{utils.escape_markdown(parent_name)}** "
            f"(`{user_info._parent}`)."
        )
        if user_id == ctx.author.id:
            output = (
                f"Your parent is **{utils.escape_markdown(parent_name)}** "
                f"(`{user_info._parent}`)."
            )
        await vbu.embeddify(ctx, output, allowed_mentions=discord.AllowedMentions.none())

    @commands.command(
        aliases=['treesize', 'fs', 'ts'],
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="user",
                    description="The user who you want to check the family size of.",
                    type=discord.ApplicationCommandOptionType.user,
                    required=False,
                ),
            ],
        ),
    )
    @commands.defer()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @vbu.checks.bot_is_ready()
    @commands.guild_only()
    @commands.bot_has_permissions(send_messages=True)
    async def familysize(
            self,
            ctx: vbu.Context,
            user: Optional[vbu.converters.UserID] = None):
        """
        Gives you the size of your family tree.
        """

        # Get the user's info
        user_id = user or ctx.author.id
        user_name = await utils.DiscordNameManager.fetch_name_by_id(self.bot, user_id)
        user_info = utils.FamilyTreeMember.get(user_id, utils.get_family_guild_id(ctx))

        # Get size
        size = user_info.family_member_count

        # Output
        output = (
            f"There {'are' if size > 1 else 'is'} {size} {'people' if size > 1 else 'person'} "
            f"in **{utils.escape_markdown(user_name)}**'s family tree."
        )
        if user_id == ctx.author.id:
            output = (
                f"There {'are' if size > 1 else 'is'} {size} "
                f"{'people' if size > 1 else 'person'} in your family tree."
            )
        await vbu.embeddify(ctx, output, allowed_mentions=discord.AllowedMentions.none())

    @commands.command(
        aliases=['relation'],
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="user",
                    description="The first user who you want to check the relation of.",
                    type=discord.ApplicationCommandOptionType.user,
                ),
                discord.ApplicationCommandOption(
                    name="other",
                    description="The second user who you want to compare the first to.",
                    type=discord.ApplicationCommandOptionType.user,
                    required=False,
                ),
            ],
        ),
    )
    @commands.defer()
    @commands.cooldown(1, 3, commands.BucketType.user)
    @vbu.checks.bot_is_ready()
    @commands.bot_has_permissions(send_messages=True)
    async def relationship(
            self,
            ctx: vbu.Context,
            user: vbu.converters.UserID,
            other: Optional[vbu.converters.UserID] = None):
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
            text = vbu.format(
                (
                    "Unsurprisingly, {0:pronoun,you're,they're} pretty closely "
                    "related to {0:pronoun,yourself,themselves}."
                ),
                user_id == ctx.author.id,
            )
            return await vbu.embeddify(ctx, text)

        # Get their relation
        user_info, other_info = utils.FamilyTreeMember.get_multiple(
            user_id,
            other_id,
            guild_id=utils.get_family_guild_id(ctx),
        )
        relation = user_info.get_relation(other_info)

        # Get names
        user_name = await utils.DiscordNameManager.fetch_name_by_id(self.bot, user_id)
        other_name = await utils.DiscordNameManager.fetch_name_by_id(self.bot, other_id)

        # Output
        if relation is None:
            output = (
                f"**{utils.escape_markdown(user_name)}** is not related "
                f"to **{utils.escape_markdown(other_name)}**."
            )
            if user_id == ctx.author.id:
                output = f"You're not related to **{utils.escape_markdown(other_name)}**."
        else:
            output = (
                f"**{utils.escape_markdown(other_name)}** is "
                f"**{utils.escape_markdown(user_name)}**'s {relation}."
            )
            if user_id == ctx.author.id:
                output = f"**{utils.escape_markdown(other_name)}** is your {relation}."
        await vbu.embeddify(ctx, output, allowed_mentions=discord.AllowedMentions.none())

    @commands.command(
        aliases=['familytree', 't', 'wreath'],
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="user",
                    description="The user you want to look at the family tree for.",
                    type=discord.ApplicationCommandOptionType.user,
                    required=False,
                ),
            ],
        ),
    )
    @commands.defer()
    @commands.dynamic_cooldown(TreeCommandCooldown.cooldown, type=commands.BucketType.user)
    @vbu.checks.bot_is_ready()
    @commands.guild_only()
    @commands.bot_has_permissions(send_messages=True, attach_files=True)
    async def tree(
            self,
            ctx: vbu.Context,
            user: Optional[vbu.converters.UserID] = None):
        """
        Get the tree of blood-related family members for a user.
        """

        lock = self.get_lock(ctx.author.id)
        if lock.locked():
            return
        async with lock:
            try:
                return await self.treemaker(
                    ctx=ctx,
                    user_id=user or ctx.author.id,
                )
            except Exception:
                raise

    @commands.command(
        aliases=['st', 'stupidtree', 'fulltree', 'bt', 'stupidwreath', 'bloodwreath'],
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="user",
                    description="The user you want to look at the family tree for.",
                    type=discord.ApplicationCommandOptionType.user,
                    required=False,
                ),
            ],
        ),
    )
    @commands.defer()
    @commands.dynamic_cooldown(TreeCommandCooldown.cooldown, type=commands.BucketType.user)
    @utils.checks.has_donator_perks("can_run_bloodtree")
    @vbu.checks.bot_is_ready()
    @commands.bot_has_permissions(send_messages=True, attach_files=True)
    async def bloodtree(
            self,
            ctx: vbu.Context,
            user: Optional[vbu.converters.UserID] = None):
        """
        Get the entire family of relations for a user, including non-blood relations.
        """

        lock = self.get_lock(ctx.author.id)
        if lock.locked():
            return
        async with lock:
            try:
                return await self.treemaker(
                    ctx=ctx,
                    user_id=user or ctx.author.id,
                    stupid_tree=True,
                )
            except Exception:
                raise

    @commands.command(
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="user",
                    description="The user you want to look at the family tree for.",
                    type=discord.ApplicationCommandOptionType.user,
                    required=False,
                ),
            ],
        ),
    )
    @commands.defer()
    @commands.dynamic_cooldown(TreeCommandCooldown.cooldown, type=commands.BucketType.user)
    @vbu.checks.bot_is_ready()
    async def rawtree(
            self,
            ctx: vbu.Context,
            user: Optional[vbu.converters.UserID] = None):
        """
        Get the entire family of relations for a user, including non-blood relations.
        """

        lock = self.get_lock(ctx.author.id)
        if lock.locked():
            return
        async with lock:
            try:
                return await self.treemaker(
                    ctx=ctx,
                    user_id=user or ctx.author.id,
                    stupid_tree=True,
                    send_dot=True,
                )
            except Exception:
                raise

    async def treemaker(
            self,
            ctx: vbu.Context,
            user_id: int,
            stupid_tree: bool = False,
            *,
            send_dot: bool = False):
        """
        Handles the generation and sending of the tree to the user.
        """

        # Get their family tree
        user_info = utils.FamilyTreeMember.get(user_id, utils.get_family_guild_id(ctx))
        user_name = await utils.DiscordNameManager.fetch_name_by_id(self.bot, user_id)

        # Make sure they have one
        if user_info.is_empty:
            if user_id == ctx.author.id:
                return await ctx.send("You have no family to put into a tree .-.")
            return await ctx.send(
                f"**{utils.escape_markdown(user_name)}** has no family to put into a tree .-.",
                allowed_mentions=discord.AllowedMentions.none(),
            )

        # Get their customisations
        async with vbu.Database() as db:
            customisations = await utils.CustomisedTreeUser.fetch_by_id(db, ctx.author.id)

        # Get their dot script
        if not isinstance(ctx, commands.SlashContext):
            await ctx.trigger_typing()
        if stupid_tree:
            dot_code = await user_info.to_full_dot_script(self.bot, customisations)
        else:
            dot_code = await user_info.to_dot_script(self.bot, customisations)

        # Write the dot to a file
        filename_id = str(uuid4())
        dot_filename = f'{self.bot.config["tree_file_location"]}/{filename_id}.gz'
        try:
            with open(dot_filename, 'w', encoding='utf-8') as a:
                a.write(dot_code)
        except Exception as e:
            self.logger.error(f"Could not write to {dot_filename}")
            raise e
        if send_dot:
            file = discord.File(dot_filename)
            await ctx.send(file=file)

        # Convert to an image
        # http://www.graphviz.org/doc/info/output.html#d:png
        image_filename = f'{self.bot.config["tree_file_location"].rstrip("/")}/{filename_id}.png'

        # if perks.tree_render_quality >= 1:
        format_rendering_option = '-Tpng:cairo'  # normal colour, and antialising
        # else:
        #     format_rendering_option = '-Tpng:gd'  # normal colour, no antialising

        dot = await asyncio.create_subprocess_exec(
            'dot',
            format_rendering_option,
            dot_filename,
            '-o',
            image_filename,
            '-Gcharset=UTF-8',
        )
        await asyncio.wait_for(dot.wait(), 30.0)

        # Kill subprocess
        try:
            dot.kill()
        except ProcessLookupError:
            pass  # It already died
        except Exception:
            raise

        # Send file
        try:
            file = discord.File(image_filename)
        except FileNotFoundError:
            return await ctx.send((
                "I was unable to send your family tree image - "
                "please try again later."
            ))
        text = "[Click here](https://marriagebot.xyz/) to customise your tree."
        if not stupid_tree:
            text += (
                f" Use `/bloodtree` for your _entire_ family, "
                "including non-blood relatives."
            )
        await vbu.embeddify(ctx, text, file=file)

        # Delete the files
        asyncio.create_task(asyncio.create_subprocess_exec('rm', dot_filename))
        asyncio.create_task(asyncio.create_subprocess_exec('rm', image_filename))


def setup(bot: utils.types.Bot):
    x = Information(bot)
    bot.add_cog(x)
