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

import novus as n
from novus import types as t
from novus.ext import client
from novus.ext import database as db
from novus.utils import CommandDefault
from novus.utils import Localization as LC

import utils as u


class Information(client.Plugin):

    @client.command(
        # TRANSLATORS: Command name
        name_localizations=LC._("partners"),
        options=[
            n.ApplicationCommandOption(
                name="user",
                description="The user whose partners you want to see.",
                type=n.ApplicationOptionType.USER,
                # TRANSLATORS: Option name (/partners user?)
                name_localizations=LC._("user"),
                # TRANSLATORS: Option name description (/partners user?)
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
                # TRANSLATORS: Option name (/children user?)
                name_localizations=LC._("user"),
                # TRANSLATORS: Option name description (/children user?)
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
                # TRANSLATORS: Option name (/parent user?)
                name_localizations=LC._("user"),
                # TRANSLATORS: Option name description (/parent user?)
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
        for _, span_user in ft.span(add_parent=True, add_partners=True, add_partner_parents=True):
            span.add(span_user)
            await asyncio.sleep(0)
        size = len(span)

        # Output
        if size == 1:
            output = (
                ctx._("There is **1** person in {user}'s family tree.")
                .format(user=user.mention)
            )
        else:
            output = (
                ctx._("There are **{number}** people in {user}'s family tree.")
                .format(user=user.mention, number=size)
            )
        await ctx.send(embeds=u.e(output))

    # @client.command(name="tree")
    # async def tree(self, ctx: t.CommandI) -> None:
    #     """
    #     Elit duis aute velit cupidatat excepteur enim esse culpa ex reprehenderit sint consectetur.
    #     """

    #     ...

    # @client.command(name="bloodtree")
    # async def bloodtree(self, ctx: t.CommandI) -> None:
    #     """
    #     Cupidatat sed id proident id excepteur veniam ut eu aliquip mollit nisi aute enim culpa ex commodo.
    #     """

    #     ...
