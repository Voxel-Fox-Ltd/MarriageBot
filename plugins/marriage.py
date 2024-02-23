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


class Marriage(client.Plugin):

    @client.command(
        # TRANSLATORS: Command name
        name_localizations=LC._("marry"),
        options=[
            n.ApplicationCommandOption(
                name="user",
                description="The user that you want to marry.",
                type=n.ApplicationOptionType.user,
                # TRANSLATORS: Option name (/marry user)
                name_localizations=LC._("user"),
                # TRANSLATORS: Option name description (/marry user)
                description_localizations=LC._("The user that you want to marry."),
            )
        ],
        # TRANSLATORS: Command description
        description_localizations=LC._("Propose to another user."),
        dm_permission=False,
    )
    async def marry(self, ctx: t.CommandGI, user: n.GuildMember) -> None:
        """
        Propose to another user.
        """

        await u.handle_proposal(
            self.bot,
            ctx,
            user,
            ctx._("Hey {user}, {author} wants to marry you! What do you say?"),
            "MARRY",
        )

    @client.command(
        # TRANSLATORS: Command name
        name_localizations=LC._("divorce"),
        # TRANSLATORS: Command description
        description_localizations=LC._("Divorce one of your partners."),
        dm_permission=False,
    )
    async def divorce(self, ctx: t.CommandGI) -> None:
        """
        Divorce one of your partners.
        """

        async with db.Database.acquire() as conn:
            partners = await u.FamilyMember.fetch_partners(
                conn,
                ctx.user,
                u.get_guild_id(self.bot, ctx),
            )
            names = await u.get_names(conn, *[i[0] for i in partners])

        if not names:
            return await ctx.send(
                embeds=u.e(ctx._("You don't have any partners right now :<")),
                ephemeral=True,
            )

        return await ctx.send(
            embeds=u.e(ctx._("Which of your partners do you want to divorce?")),
            components=[
                n.ActionRow([
                    n.StringSelectMenu(
                        custom_id=f"DIVORCE {ctx.user.id}",
                        options=[
                            n.SelectOption(label=o, value=str(i))
                            for i, o in names.items()
                        ],
                    ),
                ]),
            ],
        )

    @client.event.filtered_component(r"DIVORCE \d+")
    async def divorce_dropdown_clicked(self, ctx: t.ComponentGI) -> None:
        """
        Pinged when a divorce button is clicked.
        """

        # Make sure that the user who clicked the button is the same user
        # that the button was made for
        # It SHOULD be because the message is ephemeral, but we should check
        _, required_user_id_str = ctx.data.custom_id.split(" ")
        required_user_id = int(required_user_id_str)
        if required_user_id != ctx.user.id:
            await ctx.send(
                ctx._("You cannot interact with these buttons."),
                ephemeral=True,
            )
            return

        # Divorce them from whomever they clicked on
        clicked_user_str = ctx.data.values[0].value
        clicked_user = int(clicked_user_str)
        ft = u.FamilyMember.get(ctx.user.id, guild_id=u.get_guild_id(self.bot, ctx))
        probable_success = clicked_user in ft._partner_ids
        async with db.Database.acquire() as conn:
            await ft.db.remove_partner(conn, u.FamilyMember.get(clicked_user))

        # And done
        if probable_success:
            await ctx.update(
                embeds=u.e(
                    ctx._("You have been divorced from {user} :(")
                    .format(user=f"<@{clicked_user}>")
                ),
                components=None,
            )
            return
        await ctx.update(
            embeds=u.e(
                ctx._("You have been divorced from {user} :(")
                .format(user=f"<@{clicked_user}>")
            ),
            components=None,
        )
        return
