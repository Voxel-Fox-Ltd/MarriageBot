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
from novus.utils import Localization as LC

from . import utils as u


class Misc(client.Plugin):

    @client.command(
        # TRANSLATORS: Command name
        name_localizations=LC._("info"),
        # TRANSLATORS: Command description
        description_localizations=LC._("Give you information about the bot."),
    )
    async def info(self, ctx: t.CommandI) -> None:
        """
        Give you information about the bot.
        """

        embed = n.Embed(
            title="MarriageBot",
            description=ctx._(
                "MarriageBot is a bot that allows users to marry, divorce, and have children with "
                "other users. It also features a unique family tree system that allows users to "
                "view their family history and relationships.\n"
                "-# MarriageBot is being maintained by [Voxel Fox](https://voxelfox.co.uk)."
            ),
        ).set_image(
            "https://voxelfox.co.uk/static/images/marriagebot/tree.png"
        ).add_field(
            ctx._("Family Tree Members"),
            format(len(u.FamilyMember.ALL_MEMBERS), ","),
            inline=True,
        )
        await ctx.send(
            embeds=[embed],
            components=[
                n.ActionRow([
                    n.Button(
                        style=n.ButtonStyle.LINK,
                        label=ctx._("Donate"),
                        url="https://voxelfox.co.uk/portal/marriagebot",
                    ),
                    n.Button(
                        style=n.ButtonStyle.LINK,
                        label=ctx._("Support Server"),
                        url="https://discord.gg/voxelfox",
                    ),
                    n.Button(
                        style=n.ButtonStyle.LINK,
                        label="Voxel Fox",
                        url="https://voxelfox.co.uk",
                    ),
                ])
            ],
        )

    @client.command(
        # TRANSLATORS: Command name
        name_localizations=LC._("perks"),
        # TRANSLATORS: Command description
        description_localizations=LC._("Give you information about the bot's premium perks."),
    )
    async def perks(self, ctx: t.CommandI) -> None:
        """
        Give you information about the bot's premium perks.
        """

        await self.donate(ctx)

    @client.command(
        # TRANSLATORS: Command name
        name_localizations=LC._("donate"),
        # TRANSLATORS: Command description
        description_localizations=LC._("Give you information about the bot's donation options."),
    )
    async def donate(self, ctx: t.CommandI) -> None:
        """
        Give you information about the bot's donation options.
        """

        def gcm(c: str) -> str:
            """Get command mention"""

            cm = self.bot.get_command(c)
            if cm is None:
                return f"`/{c}`"
            return cm.mention

        embed = n.Embed(
            title=ctx._("Support MarriageBot"),
            description=ctx._(
                "If you enjoy MarriageBot, please consider donating to support its ongoing "
                "maintainance, development, and hosting costs.\n"
                "MarriageBot isn't a small bot by any means, and keeping it going requires a lot "
                "of time and resources behind the scenes."
            ),
        ).add_field(
            name=ctx._("Donation Perks"),
            value=ctx._(
                "By supporting MarriageBot, you gain access to exclusive perks depending on your "
                "subscription level:\n"
                "* Default\n"
                "  * 5 children\n"
                "  * 1 partner\n"
                "* T1\n"
                "  * 10 children\n"
                "  * 2 partners\n"
                "  * Access to {disownall_c}\n"
                "* T2\n"
                "  * 15 children\n"
                "  * 4 partners\n"
                "  * Access to {disownall_c}\n"
                "  * Access to {fulltree_c}\n"
                "* T3\n"
                "  * 20 children\n"
                "  * 8 partners\n"
                "  * Access to {disownall_c}\n"
                "  * Access to {fulltree_c}\n"
                "In addition, you can buy MarriageBot Gold for your server, which lets your "
                "server have its own family tree, and gives you access to the force commands!\n"
                "* Default\n"
                "  * Global tree\n"
                "* Gold\n"
                "  * Server-specific tree\n"
                "  * Access to the force commands ({forcedivorce_c}, {forcemarry_c}, "
                "{forceadopt_c}, {forcerunaway_c})\n"
                "  * Access to {incest_c}\n"
                "  * T3 perks for all of your server members\n"
            ).format(
                disownall_c=gcm("disownall"),
                fulltree_c=gcm("fulltree"),
                forcedivorce_c=gcm("force divorce"),
                forcemarry_c=gcm("force marry"),
                forceadopt_c=gcm("force adopt"),
                forcerunaway_c=gcm("force runaway"),
                incest_c=gcm("guild-settings incest"),
            ),
            inline=False,
        ).add_field(
            name=ctx._("How to Support"),
            value=ctx._(
                "Subscriptions can be taken out on the "
                "[Voxel Fox website](https://voxelfox.co.uk/portal/marriagebot) :3"
            ),
            inline=False,
        )
        embed.set_footer(text=ctx._("Thank you for considering supporting MarriageBot!"))
        await ctx.send(
            embeds=[embed],
            components=[
                n.ActionRow([
                    n.Button(
                        style=n.ButtonStyle.LINK,
                        label=ctx._("Donate"),
                        url="https://voxelfox.co.uk/portal/marriagebot",
                    ),
                ])
            ],
        )
