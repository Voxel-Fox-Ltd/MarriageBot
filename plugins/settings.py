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


class Settings(client.Plugin):

    @client.event.filtered_component(r"^ENABLE_GOLD$")
    async def on_enable_gold_button_press(self, ctx: t.ComponentGI) -> None:
        """
        Pinged when a user clicks the enable gold button.
        """

        if not ctx.guild:
            return await ctx.send("This is only available from within servers.")
        async with db.Database.acquire() as conn:
            available = await u.get_gold_purchased(ctx, conn)
        if available:
            await self.guild_specific_families_guild_settings(ctx, 1)
        else:
            return await ctx.send(ctx._("Gold has not been purchased for this guild."))

    @client.command(
        name="guild-settings guild-specific-families",
        description="Set whether or not guild-specific families are enabled for this guild.",
        type=n.ApplicationCommandType.CHAT_INPUT,
        options=[
            n.ApplicationCommandOption(
                name="enabled",
                description="Whether or not guild-specific families is enabled.",
                type=n.ApplicationOptionType.INTEGER,
                choices=[
                    n.ApplicationCommandChoice(
                        name="Enabled",
                        value=1,
                        # TRANSLATORS: Enable/disable setting for a command
                        name_localizations=LC._("Enabled"),
                    ),
                    n.ApplicationCommandChoice(
                        name="Disabled",
                        value=0,
                        # TRANSLATORS: Enable/disable setting for a command
                        name_localizations=LC._("Disabled"),
                    ),
                ],
            )
        ],
        dm_permission=False,
        default_member_permissions=n.Permissions(manage_members=True),
        # TRANSLATORS: Command name
        name_localizations=LC._("guild-settings guild-specific-families"),
        # TRANSLATORS: Command description
        description_localizations=LC._("Set whether or not guild-specific families are enabled for this guild."),
    )
    async def guild_specific_families_guild_settings(self, ctx: t.CommandGI, enabled: int) -> None:
        """
        Set whether or not guild-specific families are enabled for this guild.
        """

        async with db.Database.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO
                    guild_settings
                    (
                        guild_id,
                        guild_specific_families
                    )
                VALUES
                    ($1, $2)
                ON CONFLICT
                    (guild_id)
                DO UPDATE
                SET
                    guild_specific_families = excluded.guild_specific_families
                """,
                ctx.guild.id,
                bool(enabled),
            )

        command = self.guild_specific_families_guild_settings
        if enabled:
            await ctx.send(
                ctx._(
                    "Guild-specific families are now **enabled** in this guild, and you can now "
                    "use the force commands.\nPlease note that this is a completely seperate tree "
                    "than the global MarriageBot tree.\n\nYou can switch back to the global tree "
                    "by using the {guild_specific_command} command :3"
                ).format(command.mention)
            )
        else:
            await ctx.send(
                ctx._(
                    "Guild-specific families are now **disabled** in this guild. You are now "
                    "switched back to the global MarriageBot tree.\n\nYou can switch back to your "
                    "guild-specific tree by using the {guild_specific_command} command :3"
                ).format(command.mention)
            )

    @client.command(
        name="guild-settings incest",
        description="Set whether or not incest is enabled for this guild.",
        type=n.ApplicationCommandType.CHAT_INPUT,
        options=[
            n.ApplicationCommandOption(
                name="enabled",
                description="Whether or not incest is enabled.",
                type=n.ApplicationOptionType.INTEGER,
                choices=[
                    n.ApplicationCommandChoice(
                        name="Enabled",
                        value=1,
                        # TRANSLATORS: Enable/disable setting for a command
                        name_localizations=LC._("Enabled"),
                    ),
                    n.ApplicationCommandChoice(
                        name="Disabled",
                        value=0,
                        # TRANSLATORS: Enable/disable setting for a command
                        name_localizations=LC._("Disabled"),
                    ),
                ],
            )
        ],
        dm_permission=False,
        default_member_permissions=n.Permissions(manage_members=True),
        # TRANSLATORS: Command name
        name_localizations=LC._("guild-settings incest"),
        # TRANSLATORS: Command description
        description_localizations=LC._("Set whether or not incest is enabled for this guild."),
    )
    async def incest_guild_settings(self, ctx: t.CommandGI, enabled: int) -> None:
        """
        Set whether or not incest is enabled for this guild.
        """

        # See if gold is enabled
        guild_id, gold_available = await u.get_guild_id_and_gold(self.bot, ctx)
        if guild_id == 0:
            components = u.get_upsell_components(ctx, gold=True, enable_gold_button=gold_available)
            return await ctx.send(
                ctx._("This command can only be run with MarriageBot Gold enabled!"),
                components=components,
            )

        async with db.Database.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO
                    guild_settings (guild_id, allow_incest)
                    VALUES ($1, $2)
                ON CONFLICT (guild_id)
                DO UPDATE
                SET
                    allow_incest = excluded.allow_incest""",
                ctx.guild.id,
                bool(enabled),
            )
        guild_specific_command = self.guild_specific_families_guild_settings.mention
        if enabled:
            await ctx.send(
                ctx._(
                    "Incest is now **enabled** in this guild.\n\nPlease note that this only "
                    "applies to your guild-specific tree - if {guild_specific_command} is enabled."
                ).format(guild_specific_command=guild_specific_command)
            )
        else:
            await ctx.send(ctx._("Incest is now **disabled** in this guild."))

    @client.command(
        name="guild-settings simulation-gifs",
        description="Set whether or not simulation GIFs are enabled in this guild.",
        type=n.ApplicationCommandType.CHAT_INPUT,
        options=[
            n.ApplicationCommandOption(
                name="enabled",
                description="Whether or not this is enabled.",
                type=n.ApplicationOptionType.INTEGER,
                choices=[
                    n.ApplicationCommandChoice(
                        name="Enabled",
                        value=1,
                        # TRANSLATORS: Enable/disable setting for a command
                        name_localizations=LC._("Enabled"),
                    ),
                    n.ApplicationCommandChoice(
                        name="Disabled",
                        value=0,
                        # TRANSLATORS: Enable/disable setting for a command
                        name_localizations=LC._("Disabled"),
                    ),
                ],
            )
        ],
        dm_permission=False,
        default_member_permissions=n.Permissions(manage_members=True),
        # TRANSLATORS: Command name
        name_localizations=LC._("guild-settings simulation-gifs"),
        # TRANSLATORS: Command description
        description_localizations=LC._("Set whether or not simulation GIFs are enabled in this guild."),
    )
    async def simulation_gifs_guild_settings(self, ctx: t.CommandGI, enabled: int) -> None:
        """
        Set whether or not simulation GIFs are enabled in this guild.
        """

        async with db.Database.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO
                    guild_settings (guild_id, gifs_enabled)
                    VALUES ($1, $2)
                ON CONFLICT (guild_id)
                DO UPDATE
                SET
                    gifs_enabled = excluded.gifs_enabled""",
                ctx.guild.id,
                bool(enabled),
            )
        if enabled:
            await ctx.send(ctx._("GIFs for the simulation commands are now **enabled**."))
        else:
            await ctx.send(ctx._("GIFs for the simulation commands are now **disabled**."))

    # @client.command(
    #     name="",
    #     description="",
    #     type=n.ApplicationCommandType.CHAT_INPUT,
    #     dm_permission=False,
    #     default_member_permissions=n.Permissions(manage_members=True),
    #     # TRANSLATORS: Command name
    #     name_localizations=LC._(""),
    #     # TRANSLATORS: Command description
    #     description_localizations=LC._(""),
    # )
    # async def test(self, ctx: t.CommandGI) -> None:
    #     pass
