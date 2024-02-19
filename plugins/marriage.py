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

import time
import itertools

import novus as n
from novus import types as t
from novus.utils import Localization as LC
from novus.ext import client

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

        # See if they're the same person or a blacklisted user
        if ctx.user == user:
            return await ctx.send(ctx._("You can't marry yourself :/"))
        if user.bot:
            return await ctx.send(ctx._("You can't marry bots :/"))
        self.log.info(u.ProposalLock.PROPOSAL_LOCKS)
        match u.ProposalLock.locked(ctx.user.id, user.id):
            case 0:
                return await ctx.send(
                    ctx._("You're already waiting on a proposal."),
                    ephemeral=True,
                )
            case 1:
                return await ctx.send(
                    (
                        ctx._("{user} is already waiting on a proposal.")
                        .format(user=user.mention)
                    ),
                    ephemeral=True,
                )
        unlock_f = await u.ProposalLock.lock(ctx.user.id, user.id)
        if unlock_f is None:
            return  # Failed to lock
        await ctx.defer()

        # See if they're already related
        guild_id: int = ctx.guild.id if self.bot.config.gold else 0
        author_ft, user_ft = u.FamilyMember.get_multiple(ctx.user.id, user.id, guild_id=guild_id)
        if author_ft.get_related(user_ft):
            unlock_f()
            return await ctx.send(
                (
                    ctx._("You and {user} are already related!")
                    .format(user=user.mention)
                ),
                allowed_mentions=n.AllowedMentions.none(),
            )

        # See if they're above a certain family size limit
        family_size_limit: int = 2_000 if self.bot.config.gold else 750
        kwargs = {
            "people_list": None,
            "add_parent": True,
            "add_partners": True,
            "add_partner_parents": True,
        }
        for counter, _ in enumerate(itertools.chain(
                author_ft.span(**kwargs),
                user_ft.span(**kwargs))):
            if counter > family_size_limit:
                unlock_f()
                return await ctx.send(
                    ctx._(
                        "You can't do that! If your families combine, you'd "
                        "have over {family_size} members in your tree!"
                    )
                    .format(family_size=family_size_limit)
                )

        # Send proposal message
        time_ = int(time.time() + u.PROPOSAL_TIMEOUT)
        m = await ctx.followup(
            (
                ctx._("Hey {user}, {author} wants to propose to you! What do you say?")
                .format(user=user.mention, author=ctx.user.mention)
            ),
            components=[
                n.ActionRow([
                    n.Button(
                        ctx._("Accept"),
                        style=n.ButtonStyle.green,
                        custom_id=f"PROPOSE MARRY 1 {ctx.user.id} {user.id} {time_}",
                    ),
                    n.Button(
                        ctx._("Decline"),
                        style=n.ButtonStyle.red,
                        custom_id=f"PROPOSE MARRY 0 {ctx.user.id} {user.id} {time_}",
                    ),
                ]),
            ],
        )
        u.AutoDelete.autodelete(
            m, time_,
            content=(
                ctx._("Sorry, {author}, your proposal to {user} has timed out!")
                .format(author=ctx.user.mention, user=user.mention)
            ),
            components=None,
        )

    @client.command(
        # TRANSLATORS: Command name; must be lowercase
        name_localizations=LC._("divorce"),
        # TRANSLATORS: Command description
        description_localizations=LC._("Divorce one of your partners."),
        dm_permission=False,
    )
    async def divorce(self, ctx: t.CommandGI) -> None:
        """
        Divorce one of your partners.
        """

        ...
