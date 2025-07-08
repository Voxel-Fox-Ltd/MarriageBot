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

from . import utils as u


class Parents(client.Plugin):

    @client.command(
        # TRANSLATORS: Command name
        name_localizations=LC._("adopt"),
        options=[
            n.ApplicationCommandOption(
                name="user",
                description="The user that you want to adopt.",
                type=n.ApplicationOptionType.USER,
                # TRANSLATORS: Command option name (/adopt user)
                name_localizations=LC._("user"),
                # TRANSLATORS: Command option name description (/adopt user)
                description_localizations=LC._("The user that you want to adopt."),
            )
        ],
        # TRANSLATORS: Command description
        description_localizations=LC._("Ask to adopt another user."),
        dm_permission=False,
    )
    async def adopt(self, ctx: t.CommandGI, user: n.GuildMember) -> None:
        """
        Ask to adopt another user.
        """

        await u.handle_proposal(
            self.bot,
            ctx,
            user,
            ctx._("Hey {user}, {author} wants to adopt you! What do you say?"),
            "ADOPT",
        )

    @client.command(
        # TRANSLATORS: Command name
        name="makeparent",
        name_localizations=LC._("makeparent"),
        options=[
            n.ApplicationCommandOption(
                name="user",
                description="The user that you want to make into your parent.",
                type=n.ApplicationOptionType.USER,
                # TRANSLATORS: Command option name (/makeparent user)
                name_localizations=LC._("user"),
                # TRANSLATORS: Command option name description (/makeparent user)
                description_localizations=LC._("The user that you want to make into your parent."),
            )
        ],
        # TRANSLATORS: Command description
        description_localizations=LC._("Ask to make another user into your parent."),
        dm_permission=False,
    )
    async def makeparent(self, ctx: t.CommandGI, user: n.GuildMember) -> None:
        """
        Ask to make another user into your parent.
        """

        await u.handle_proposal(
            self.bot,
            ctx,
            user,
            ctx._("Hey {user}, {author} wants you to be their parent! What do you say?"),
            "MAKEPARENT",
        )

    @client.command(
        # TRANSLATORS: Command name
        name_localizations=LC._("runaway"),
        # TRANSLATORS: Command description
        description_localizations=LC._("Run away from your parent."),
        dm_permission=False,
    )
    async def runaway(self, ctx: t.CommandI) -> None:
        """
        Run away from your parent.
        """

        guild_id = await u.get_guild_id(self.bot, ctx)
        ft = u.FamilyMember.get(ctx.user, guild_id)

        if not ft.parent:
            return await ctx.send(
                embeds=u.e(ctx._("You don't have any children right now :<"), gold=guild_id != 0),
                ephemeral=True,
            )

        async with db.Database.acquire() as conn:
            parent = await ft.db.remove_parent(conn)
            if not parent:
                raise TypeError("Somehow, they both did have and didn't have a parent.")

        return await ctx.send(
            embeds=u.e(
                (
                    ctx._("You have run away from {user} :(")
                    .format(user=f"<@{parent.id}>")
                ),
                gold=guild_id != 0,
            ),
        )

    @client.command(
        # TRANSLATORS: Command name
        name_localizations=LC._("disown"),
        # TRANSLATORS: Command description
        description_localizations=LC._("Disown one of your children."),
        dm_permission=False,
    )
    async def disown(self, ctx: t.CommandGI) -> None:
        """
        Disown one of your children.
        """

        async with db.Database.acquire() as conn:
            guild_id = await u.get_guild_id(self.bot, ctx, conn)
            children = await u.FamilyMember.fetch_children(
                conn,
                ctx.user,
                guild_id,
            )
            names = await u.get_names(conn, *[i[0] for i in children])

        if not names:
            return await ctx.send(
                embeds=u.e(ctx._("You don't have any children right now :<"), gold=guild_id != 0),
                ephemeral=True,
            )

        return await ctx.send(
            embeds=u.e(ctx._("Which of your children do you want to disown?"), gold=guild_id != 0),
            components=[
                n.ActionRow([
                    n.StringSelectMenu(
                        custom_id=f"DISOWN {ctx.user.id}",
                        options=[
                            n.SelectOption(label=o, value=str(i))
                            for i, o in names.items()
                        ],
                    ),
                ]),
            ],
        )

    @client.event.filtered_component(r"DISOWN \d+")
    async def disown_dropdown_clicked(self, ctx: t.ComponentGI) -> None:
        """
        Pinged when a disown button is clicked.
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
        guild_id = await u.get_guild_id(self.bot, ctx)
        ft = u.FamilyMember.get(ctx.user.id, guild_id=guild_id)
        probable_success = clicked_user in ft._partner_ids
        async with db.Database.acquire() as conn:
            await ft.db.remove_child(conn, u.FamilyMember.get(clicked_user))

        # And done
        if probable_success:
            await ctx.update(
                embeds=u.e(
                    (
                        ctx._("You have now disowned {user} :(")
                        .format(user=f"<@{clicked_user}>")
                    ),
                    gold=guild_id != 0,
                ),
                components=None,
            )
            return
        await ctx.update(
            embeds=u.e(
                (
                    ctx._("You have now disowned {user} :(")
                    .format(user=f"<@{clicked_user}>")
                ),
                gold=guild_id != 0,
            ),
            components=None,
        )
        return
