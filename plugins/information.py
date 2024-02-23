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

import novus as n
from novus import types as t
from novus.ext import client
from novus.ext import database as db
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
                type=n.ApplicationOptionType.user,
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
            user: n.User | n.GuildMember | None = None) -> None:
        """
        Shows you a list of partners for a user.
        """

        # Get user and their partner names
        user = user or ctx.user
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

    # @client.command(name="children")
    # async def children(self, ctx: t.CommandI) -> None:
    #     """
    #     Dolor eiusmod do et cillum nulla velit enim do.
    #     """

    #     ...

    # @client.command(name="parent")
    # async def parent(self, ctx: t.CommandI) -> None:
    #     """
    #     Lorem ipsum in labore labore in voluptate ex ullamco qui eu fugiat.
    #     """

    #     ...

    # @client.command(name="familysize")
    # async def familysize(self, ctx: t.CommandI) -> None:
    #     """
    #     Lorem ipsum pariatur ea laborum elit excepteur minim officia culpa non ullamco sed excepteur et.
    #     """

    #     ...

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
