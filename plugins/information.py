"""
Copyright (c) Kae Bartlett

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""

from __future__ import annotations

import asyncio
import os
import pathlib
import uuid

import novus as n
from novus import types as t
from novus.ext import client
from novus.ext import database as db
from novus.utils import CommandDefault
from novus.utils import Localization as LC

from . import utils as u


class Information(client.Plugin):

    TREE_FOLDER = pathlib.Path("./_temp/")

    @client.command(
        # TRANSLATORS: Command name
        name_localizations=LC._("partners"),
        options=[
            n.ApplicationCommandOption(
                name="user",
                description="The user whose partners you want to see.",
                type=n.ApplicationOptionType.USER,
                # TRANSLATORS: Command option name (/partners [user])
                name_localizations=LC._("user"),
                # TRANSLATORS: Command option name description (/partners [user])
                description_localizations=LC._("The user whose partners you want to see."),
                required=False,
            )
        ],
        # TRANSLATORS: Command description
        description_localizations=LC._("Shows you a list of partners for a user."),
        dm_permission=False,
    )
    async def partners(
            self,
            ctx: t.CommandI,
            user: n.User = CommandDefault.AUTHOR) -> None:
        """
        Shows you a list of partners for a user.
        """

        # Get user and their partner names
        async with db.Database.acquire() as conn:
            partners = await u.FamilyMember.fetch_partners(
                conn,
                user,
                u.get_guild_id(self.bot, ctx),
            )
            partner_names = await u.get_names(conn, *[i[0] for i in partners])

        # Sort into a dict
        partner_info = {
            i[0]: (partner_names[i[0]], i[1])
            for i in partners
        }

        # No partners
        if not partner_info:
            if user == ctx.user:
                return await ctx.send(
                    embeds=u.e(ctx._("You don't have any partners right now :<")),
                )
            return await ctx.send(
                embeds=u.e(
                    ctx._("{user} doesn't have any partners right now :<")
                    .format(user=user.mention)
                ),
            )

        # One partner
        if len(partner_info) == 1:
            pi = list(partner_info.values())[0]
            return await ctx.send(
                embeds=u.e(
                    ctx._("{user} is married to **{partner}** ({timestamp}).")
                    .format(user=user.mention, partner=pi[0], timestamp=pi[1].format("R"))
                ),
            )

        # Multiple partners
        lines = "\n".join([
            f"* **{i[0]}** ({i[1].format('R')})"
            for i in partner_info.values()
        ])
        return await ctx.send(
            embeds=u.e(
                ctx._("{user} is married to:").format(user=user.mention)
                + "\n"
                + lines
            ),
        )

    @client.command(
        # TRANSLATORS: Command name
        name_localizations=LC._("children"),
        options=[
            n.ApplicationCommandOption(
                name="user",
                description="The user whose children you want to see.",
                type=n.ApplicationOptionType.USER,
                # TRANSLATORS: Command option name (/children [user])
                name_localizations=LC._("user"),
                # TRANSLATORS: Command option name description (/children [user])
                description_localizations=LC._("The user whose children you want to see."),
                required=False,
            )
        ],
        # TRANSLATORS: Command description
        description_localizations=LC._("Shows you a list of children for a user."),
        dm_permission=False,
    )
    async def children(
            self,
            ctx: t.CommandI,
            user: n.User = CommandDefault.AUTHOR) -> None:
        """
        Shows you a list of children for a user.
        """

        # Get user and their child names
        async with db.Database.acquire() as conn:
            children = await u.FamilyMember.fetch_children(
                conn,
                user,
                u.get_guild_id(self.bot, ctx),
            )
            children_names = await u.get_names(conn, *[i[0] for i in children])

        # Sort into a dict
        children_info = {
            i[0]: (children_names[i[0]], i[1])
            for i in children
        }

        # No children
        if not children_info:
            if user == ctx.user:
                return await ctx.send(
                    embeds=u.e(ctx._("You don't have any children right now :<")),
                )
            return await ctx.send(
                embeds=u.e(
                    ctx._("{user} doesn't have any children right now :<")
                    .format(user=user.mention)
                ),
            )

        # One partner
        if len(children_info) == 1:
            pi = list(children_info.values())[0]
            return await ctx.send(
                embeds=u.e(
                    ctx._("{user} is parent to **{partner}** ({timestamp}).")
                    .format(user=user.mention, partner=pi[0], timestamp=pi[1].format("R"))
                ),
            )

        # Multiple children
        lines = "\n".join([
            f"* **{i[0]}** ({i[1].format('R')})"
            for i in children_info.values()
        ])
        return await ctx.send(
            embeds=u.e(
                ctx._("{user} is parent to:").format(user=user.mention)
                + "\n"
                + lines
            ),
        )

    @client.command(
        # TRANSLATORS: Command name
        name_localizations=LC._("parent"),
        options=[
            n.ApplicationCommandOption(
                name="user",
                description="The user whose parent you want to see.",
                type=n.ApplicationOptionType.USER,
                # TRANSLATORS: Command option name (/parent [user])
                name_localizations=LC._("user"),
                # TRANSLATORS: Command option name description (/parent [user])
                description_localizations=LC._("The user whose parent you want to see."),
                required=False,
            )
        ],
        # TRANSLATORS: Command description
        description_localizations=LC._("Show you the parent for a user."),
        dm_permission=False,
    )
    async def parent(
            self,
            ctx: t.CommandI,
            user: n.User = CommandDefault.AUTHOR) -> None:
        """
        Show you the parent for a user.
        """

        # Get parent and name
        async with db.Database.acquire() as conn:
            parent = await u.FamilyMember.fetch_parent(
                conn,
                user,
                u.get_guild_id(self.bot, ctx),
            )
            parent_name: str | None = None
            if parent:
                parent_name = await u.get_name(conn, parent[0])

        # No parent
        if not parent:
            if user == ctx.user:
                return await ctx.send(
                    embeds=u.e(ctx._("You don't have a parent right now :<")),
                )
            return await ctx.send(
                embeds=u.e(
                    ctx._("{user} doesn't have a parent right now :<")
                    .format(user=user.mention)
                ),
            )
        assert parent_name

        return await ctx.send(
            embeds=u.e(
                ctx._("{user}'s parent is **{parent}** ({timestamp}).")
                .format(
                    user=user.mention,
                    parent=parent_name,
                    timestamp=parent[1].format("R")
                )
            ),
        )

    # @client.command(name="siblings")
    # async def siblings(self, ctx: t.CommandI) -> None:
    #     """
    #     Elit duis aute velit cupidatat excepteur enim esse culpa ex reprehenderit sint consectetur.
    #     """

    #     ...

    # @client.command(name="relationship")
    # async def relationship(self, ctx: t.CommandI) -> None:
    #     """
    #     Elit duis aute velit cupidatat excepteur enim esse culpa ex reprehenderit sint consectetur.
    #     """

    #     ...

    @client.command(
        options=[
            n.ApplicationCommandOption(
                name="user",
                description="The user who you want to see the family size of.",
                type=n.ApplicationOptionType.USER,
                # TRANSLATORS: Command option name (/familysize [user])
                name_localizations=LC._("user"),
                # TRANSLATORS: Command option description (/familysize [user])
                description_localizations=LC._("The user who you want to see the family size of."),
                required=False,
            ),
        ],
        # TRANSLATORS: Command name (/familysize)
        name_localizations=LC._("familysize"),
        # TRANSLATORS: Command description (/familysize)
        description_localizations=LC._("Get the family size of another user.")
    )
    async def familysize(
            self,
            ctx: t.CommandI,
            user: n.User = n.utils.CommandDefault.AUTHOR) -> None:
        """
        Get the family size of another user.
        """

        # Get the user's info and family size
        ft = u.FamilyMember.get(user.id, u.get_guild_id(self.bot, ctx))
        span = set()
        async for _, span_user in ft.span(
                add_parent=True,
                add_partners=True,
                add_partner_parents=True):
            span.add(span_user)
        size = len(span)

        # Output
        output = ctx.ngettext(
            "There is **{number}** person in {user}'s family tree, including all blood and non-blood relatives.",
            "There are **{number}** people in {user}'s family tree, including all blood and non-blood relatives.",
            size,
        )
        await ctx.send(embeds=u.e(output))

    @client.command(
        # TRANSLATORS: Command name (/tree)
        name_localizations=LC._("tree"),
        options=[
            n.ApplicationCommandOption(
                name="user",
                description="The user whose tree you want to see.",
                type=n.ApplicationOptionType.USER,
                # TRANSLATORS: Command option name (/tree [user])
                name_localizations=LC._("user"),
                description_localizations=LC._("The user whose tree you want to see."),
                required=False,
            )
        ],
        description_localizations=LC._("Show your family tree, but only blood relatives :3")
    )
    async def tree(
            self,
            ctx: t.CommandI,
            user: n.User = n.utils.CommandDefault.AUTHOR) -> None:
        """
        Show your family tree, but only blood relatives :3
        """

        await self.treemaker(ctx, user.id)

    @client.command(
        # TRANSLATORS: Command name (/fulltree)
        name_localizations=LC._("fulltree"),
        options=[
            n.ApplicationCommandOption(
                name="user",
                description="The user whose tree you want to see.",
                type=n.ApplicationOptionType.USER,
                # TRANSLATORS: Command option name (/fulltree [user])
                name_localizations=LC._("user"),
                description_localizations=LC._("The user whose tree you want to see."),
                required=False,
            )
        ],
        description_localizations=LC._("Show your entire family tree, including non-blood relatives :3")
    )
    async def fulltree(
            self,
            ctx: t.CommandI,
            user: n.User = n.utils.CommandDefault.AUTHOR) -> None:
        """
        Show your entire family tree, including non-blood relatives :3
        """

        await self.treemaker(ctx, user.id, full_tree=True)

    async def treemaker(
            self,
            ctx: t.CommandI,
            user_id: int,
            *,
            full_tree: bool = False) -> None:
        """
        Handles the generation and sending of the tree to the user.
        """

        # Get their family tree
        guild_id: int = u.get_guild_id(self.bot, ctx)
        family_member = u.FamilyMember.get(user_id, guild_id)

        # Make sure they have one
        if family_member.is_empty:
            if user_id == ctx.user.id:
                return await ctx.send(
                    embeds=u.e(ctx._("You have no family to put into a tree .-."))
                )
            return await ctx.send(
                embeds=u.e(ctx._("**{user}** has no family to put into a tree .-.")),
                allowed_mentions=n.AllowedMentions.none(),
            )
        await ctx.defer()

        # Get their customisations
        async with db.Database.acquire() as conn:
            custom = await u.CustomTree.fetch(conn, ctx.user.id)

        # Get their dot script
        kwargs = {}
        if full_tree:
            kwargs = {
                "add_partners": True,
                "add_partners": True,
                "add_partner_parents": True,
            }
        try:
            dot_code = await asyncio.wait_for(
                family_member.to_dot_script(custom, **kwargs),
                timeout=10.0,
            )
        except asyncio.TimeoutError:
            self.log.error("Failed to create dot script within 10 seconds.")
            return

        # Write the dot to a file
        filename_id = str(uuid.uuid4())
        dot_filename = self.TREE_FOLDER / f"{filename_id}.gz"
        os.makedirs(self.TREE_FOLDER, exist_ok=True)
        try:
            with open(dot_filename, 'w', encoding='utf-8') as a:
                a.write(dot_code)
        except Exception as e:
            self.log.error(f"Could not write to {dot_filename}")
            raise e

        # Convert to an image
        # http://www.graphviz.org/doc/info/output.html#d:png
        image_filename = self.TREE_FOLDER / f"{filename_id}.png"

        format_rendering_option = "-Tpng:cairo"  # normal colour, and antialising
        # format_rendering_option = '-Tpng:gd'  # normal colour, no antialising
        # format_rendering_option = "-Tpng:cairo:gdiplus"
        # format_rendering_option = "-Tpng:gdiplus:gdiplus"

        dot = await asyncio.create_subprocess_exec(
            "dot",
            format_rendering_option,
            dot_filename,
            "-o",
            image_filename,
            "-Gcharset=UTF-8",
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
            file = n.File(image_filename, filename="tree.png")
        except FileNotFoundError:
            return await ctx.send(
                ctx._(
                    "I was unable to send your family tree image - "
                    "please try again later."
                )
            )
        text = ctx._("[Click here]({url}) to customise your tree.")
        if not full_tree:
            text += " " + (
                ctx._(
                    "Use {command_mention} for your *entire* family, "
                    "including non-blood relatives."
                )
            )
        command_mention: str
        try:
            command_mention = self.bot.get_command("fulltree").mention  # type: ignore
        except Exception:
            command_mention = "`/fulltree`"
        text = text.format(
            url="https://marriagebot.xyz/",
            command_mention=command_mention,
        )
        await ctx.send(
            embeds=u.e(text, image_url="attachment://tree.png"),
            files=[file],
        )

        # Delete the files
        asyncio.create_task(asyncio.create_subprocess_exec("rm", dot_filename))
        asyncio.create_task(asyncio.create_subprocess_exec("rm", image_filename))
