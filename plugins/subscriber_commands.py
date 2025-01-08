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

from novus import types as t
from novus.ext import client
from novus.ext import database as db
from novus.utils import Localization as LC

from . import utils as u


class SubscriberCommands(client.Plugin):

    @client.command(
        name="disownall",
        description="Disown all of your children at once.",
        # TRANSLATORS: Command name
        name_localizations=LC._("disownall"),
        # TRANSLATORS: Command description
        description_localizations=LC._("Disown all of your children at once."),
    )
    async def disownall(self, ctx: t.CommandGI) -> None:
        """
        Disown all of your children at once.
        """

        user_perks = await u.Perks.get_perks_for_user(self.bot, ctx, ctx.user.id)
        if not user_perks.can_run_disownall:
            command = u.get_command_mention(self.bot, "disown")
            await ctx.send(
                ctx._(
                    "You need to be a higher tier subscriber to run this command! "
                    "You can still use {non_perks_command} though :3"
                ).format(non_perks_command=command),
                ephemeral=True,
            )
            return

        user_ft = u.FamilyMember.get(ctx.user.id, await u.get_guild_id(self.bot, ctx))
        async with db.Database.acquire() as conn:
            for child in user_ft.children:
                await user_ft.db.remove_child(conn, child)

        await ctx.send(
            embeds=u.e(ctx._("Done! You no longer have any children :3"))
        )

    @client.command(
        name="abandon",
        description="Remove all of your family members at once.",
        # TRANSLATORS: Command name
        name_localizations=LC._("abandon"),
        # TRANSLATORS: Command description
        description_localizations=LC._("Remove all of your family members at once."),
    )
    async def abandon(self, ctx: t.CommandGI) -> None:
        """
        Remove all of your family members at once.
        """

        user_perks = await u.Perks.get_perks_for_user(self.bot, ctx, ctx.user.id)
        if not user_perks.can_run_abandon:
            divorce_c = u.get_command_mention(self.bot, "divorce")
            disown_c = u.get_command_mention(self.bot, "disown")
            runaway_c = u.get_command_mention(self.bot, "runaway")
            await ctx.send(
                ctx._(
                    "You need to be a higher tier subscriber to run this command! "
                    "You can still use {divorce}, {disown}, and {runaway} though :3"
                ).format(divorce=divorce_c, disown=disown_c, runaway=runaway_c),
                ephemeral=True,
            )
            return

        user_ft = u.FamilyMember.get(ctx.user.id, await u.get_guild_id(self.bot, ctx))
        async with db.Database.acquire() as conn:
            for child in user_ft.children:
                await user_ft.db.remove_child(conn, child)
            for partner in user_ft.partners:
                await user_ft.db.remove_partner(conn, partner)
            await user_ft.db.remove_parent(conn)

        await ctx.send(
            embeds=u.e(ctx._("Done! You no longer have any family members :3"))
        )
