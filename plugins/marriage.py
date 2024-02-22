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
        # TRANSLATORS: Command name; must be lowercase
        name_localizations=LC._("marry"),
        options=[
            n.ApplicationCommandOption(
                name="user",
                description="The user that you want to marry.",
                type=n.ApplicationOptionType.user,
                # TRANSLATORS: Option name (/marry user); must be lowercase
                name_localizations=LC._("user"),
                # TRANSLATORS: Option name description (/marry user); max 100 characters
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
        # TRANSLATORS: Command name; must be lowercase
        name_localizations=LC._("divorce"),
        # TRANSLATORS: Command description; max 100 characters
        description_localizations=LC._("Divorce one of your partners."),
        dm_permission=False,
    )
    async def divorce(self, ctx: t.CommandGI) -> None:
        """
        Divorce one of your partners.
        """

        ...
