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


class ForceCommands(client.Plugin):

    @client.command(
        name="force marry",
        description="Force two users to marry each other.",
        type=n.ApplicationCommandType.CHAT_INPUT,
        dm_permission=False,
        default_member_permissions=n.Permissions(manage_guild=True),
        options=[
            n.ApplicationCommandOption(
                name="user1",
                description="The first user that you want to set up to marry.",
                type=n.ApplicationOptionType.USER,
                # TRANSLATORS: Command option name (/force marry [user1] [user2])
                name_localizations=LC._("user1"),
                # TRANSLATORS: Command option name description
                description_localizations=LC._("The first user that you want to set up to marry."),
            ),
            n.ApplicationCommandOption(
                name="user2",
                description="The second user that you want to set up to marry.",
                type=n.ApplicationOptionType.USER,
                required=False,
                # TRANSLATORS: Command option name (/force marry [user1] [user2])
                name_localizations=LC._("user2"),
                # TRANSLATORS: Command option name description
                description_localizations=LC._("The second user that you want to set up to marry."),
            ),
        ],
        # TRANSLATORS: Command name
        name_localizations=LC._("force marry"),
        # TRANSLATORS: Command description
        description_localizations=LC._("Force two users to marry each other."),
    )
    async def marry_force(
            self,
            ctx: t.CommandGI,
            user1: n.User,
            user2: n.User = n.utils.CommandDefault.AUTHOR) -> None:
        """
        Force two users to marry each other.
        """

        guild_id, gold_available = await u.get_guild_id_and_gold(self.bot, ctx)
        if guild_id == 0:
            components = u.get_upsell_components(ctx, gold=True, enable_gold_button=gold_available)
            await ctx.send(
                ctx._(
                    (
                        "This command can only be run with MarriageBot Gold enabled! You "
                        "can still use {non_gold_command} though :3"
                    )
                ).format(non_gold_command=u.get_command_mention(self.bot, "marry")),
                components=components,
                ephemeral=True,
            )
            return

        if user1 == user2:
            await ctx.send(
                ctx._("You can't marry someone to themself :/"),
                ephemeral=True,
            )
            return

        user1_ft, user2_ft = u.FamilyMember.get_multiple(user1.id, user2.id, guild_id=guild_id)

        async with db.Database.acquire() as conn:
            await user1_ft.db.add_partner(conn, user2_ft)

        await ctx.send(
            embeds=u.e(
                ctx._("Done! Married {user1} and {user2} :3").format(
                    user1=user1.mention,
                    user2=user2.mention,
                ),
                gold=guild_id != 0,
            ),
            allowed_mentions=n.AllowedMentions.none(),
        )

    @client.command(
        name="force divorce",
        description="Force two users to divorce each other.",
        type=n.ApplicationCommandType.CHAT_INPUT,
        dm_permission=False,
        default_member_permissions=n.Permissions(manage_guild=True),
        options=[
            n.ApplicationCommandOption(
                name="user1",
                description="The first user that you want to set up to divorce.",
                type=n.ApplicationOptionType.USER,
                # TRANSLATORS: Command option name (/force divorce [user1] [user2])
                name_localizations=LC._("user1"),
                # TRANSLATORS: Command option name description
                description_localizations=LC._(
                    "The first user that you want to set up to divorce."
                ),
            ),
            n.ApplicationCommandOption(
                name="user2",
                description="The second user that you want to set up to divorce.",
                type=n.ApplicationOptionType.USER,
                # TRANSLATORS: Command option name (/force divorce [user1] [user2])
                name_localizations=LC._("user2"),
                # TRANSLATORS: Command option name description
                description_localizations=LC._(
                    "The second user that you want to set up to divorce."
                ),
            ),
        ],
        # TRANSLATORS: Command name
        name_localizations=LC._("force divorce"),
        # TRANSLATORS: Command description
        description_localizations=LC._("Force two users to divorce each other."),
    )
    async def divorce_force(
            self,
            ctx: t.CommandGI,
            user1: n.User,
            user2: n.User) -> None:
        """
        Force two users to divorce each other.
        """

        guild_id, gold_available = await u.get_guild_id_and_gold(self.bot, ctx)
        if guild_id == 0:
            components = u.get_upsell_components(ctx, gold=True, enable_gold_button=gold_available)
            await ctx.send(
                ctx._(
                    (
                        "This command can only be run with MarriageBot Gold enabled! You "
                        "can still use {non_gold_command} though :3"
                    )
                ).format(non_gold_command=u.get_command_mention(self.bot, "divorce")),
                components=components,
                ephemeral=True,
            )
            return

        user1_ft, user2_ft = u.FamilyMember.get_multiple(user1.id, user2.id, guild_id=guild_id)

        is_current_partner = user2.id in user1_ft._partner_ids

        async with db.Database.acquire() as conn:
            await user1_ft.db.remove_partner(conn, user2_ft)

        if not is_current_partner:
            await ctx.send(
                embeds=u.e(
                    ctx._(
                        (
                            "Done, even though {user1} and {user2} weren't actually married "
                            "to start with."
                        )
                    ).format(user1=user1.mention, user2=user2.mention),
                    gold=guild_id != 0,
                ),
                allowed_mentions=n.AllowedMentions.none(),
            )
            return

        await ctx.send(
            embeds=u.e(
                ctx._("Done! {user1} and {user2} are now divorced :3").format(
                    user1=user1.mention,
                    user2=user2.mention,
                )
            ),
            allowed_mentions=n.AllowedMentions.none(),
        )

    @client.command(
        name="force adopt",
        description="Force one user to adopt another.",
        type=n.ApplicationCommandType.CHAT_INPUT,
        dm_permission=False,
        default_member_permissions=n.Permissions(manage_guild=True),
        options=[
            n.ApplicationCommandOption(
                name="user1",
                description="The child for the adoption.",
                type=n.ApplicationOptionType.USER,
                # TRANSLATORS: Command option name (/force adopt [user1] [user2])
                name_localizations=LC._("user1"),
                # TRANSLATORS: Command option name description
                description_localizations=LC._("The child for the adoption"),
            ),
            n.ApplicationCommandOption(
                name="user2",
                type=n.ApplicationOptionType.USER,
                description="The parent for the adoption.",
                required=False,
                # TRANSLATORS: Command option name (/force adopt [user1] [user2])
                name_localizations=LC._("user2"),
                # TRANSLATORS: Command option name description
                description_localizations=LC._("The parent for the adoption."),
            ),
        ],
        # TRANSLATORS: Command name
        name_localizations=LC._("force adopt"),
        # TRANSLATORS: Command description
        description_localizations=LC._("Force one user to adopt another."),
    )
    async def adopt_force(
            self,
            ctx: t.CommandGI,
            user1: n.User,
            user2: n.User = n.utils.CommandDefault.AUTHOR) -> None:
        """
        Force one user to adopt another.
        """

        guild_id, gold_available = await u.get_guild_id_and_gold(self.bot, ctx)
        if guild_id == 0:
            components = u.get_upsell_components(ctx, gold=True, enable_gold_button=gold_available)
            await ctx.send(
                ctx._(
                    (
                        "This command can only be run with MarriageBot Gold enabled! You "
                        "can still use {non_gold_command} though :3"
                    )
                ).format(non_gold_command=u.get_command_mention(self.bot, "adopt")),
                components=components,
                ephemeral=True,
            )
            return

        if user1 == user2:
            await ctx.send(
                ctx._("You can't adopt someone to themself :/"),
                ephemeral=True,
            )
            return

        user1_ft, user2_ft = u.FamilyMember.get_multiple(user1.id, user2.id, guild_id=guild_id)

        if user1_ft._parent_id:
            await ctx.send(
                ctx._(
                    (
                        "{user} already has a parent! If you want to solve that too, "
                        "you can use {force_runaway_command}."
                    ).format(
                        user=user1.mention,
                        force_runaway_command=u.get_command_mention(self.bot, "force runaway"),
                    )
                ),
                ephemeral=True,
            )
            return

        async with db.Database.acquire() as conn:
            await user1_ft.db.add_parent(conn, user2_ft)

        await ctx.send(
            embeds=u.e(
                ctx._("Done! {user1} is now a child of {user2} :3").format(
                    user1=user1.mention,
                    user2=user2.mention,
                ),
                gold=guild_id != 0,
            ),
            allowed_mentions=n.AllowedMentions.none(),
        )

    @client.command(
        name="force runaway",
        description="Force a user to runaway from their parent.",
        type=n.ApplicationCommandType.CHAT_INPUT,
        dm_permission=False,
        default_member_permissions=n.Permissions(manage_guild=True),
        options=[
            n.ApplicationCommandOption(
                name="user",
                description="The user that you want to force to runaway.",
                type=n.ApplicationOptionType.USER,
                # TRANSLATORS: Command option name (/force runaway [user])
                name_localizations=LC._("user"),
                # TRANSLATORS: Command option name description
                description_localizations=LC._("The user that you want to force to runaway"),
            ),
        ],
        # TRANSLATORS: Command name
        name_localizations=LC._("force runaway"),
        # TRANSLATORS: Command description
        description_localizations=LC._("Force a user to runaway from their parent."),
    )
    async def runaway_force(
            self,
            ctx: t.CommandGI,
            user: n.User) -> None:
        """
        Force a user to runaway from their parent.
        """

        guild_id, gold_available = await u.get_guild_id_and_gold(self.bot, ctx)
        if guild_id == 0:
            components = u.get_upsell_components(ctx, gold=True, enable_gold_button=gold_available)
            await ctx.send(
                ctx._(
                    (
                        "This command can only be run with MarriageBot Gold enabled! You "
                        "can still use {non_gold_command} though :3"
                    )
                ).format(non_gold_command=u.get_command_mention(self.bot, "runaway")),
                components=components,
                ephemeral=True,
            )
            return

        user_ft = u.FamilyMember.get(user.id, guild_id=guild_id)

        async with db.Database.acquire() as conn:
            await user_ft.db.remove_parent(conn)

        await ctx.send(
            embeds=u.e(
                ctx._("Done! {user} no longer has a parent :3").format(
                    user=user.mention,
                ),
                gold=guild_id != 0,
            ),
            allowed_mentions=n.AllowedMentions.none(),
        )
