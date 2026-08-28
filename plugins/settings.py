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

    @client.command(
        name="transfer-gold",
        description="Transfer your MarriageBot Gold purchase to this server.",
        # TRANSLATORS: Command name
        name_localizations=LC._("transfer-gold"),
        # TRANSLATORS: Command description
        description_localizations=LC._("Transfer your MarriageBot Gold purchase to this server."),
        dm_permission=False
    )
    async def transfer_gold(self, ctx: t.CommandGI) -> None:
        """
        Transfer your MarriageBot Gold purchase to this server.
        """

        # Make sure we're in a guild
        if not ctx.guild:
            return  # Silently fail
        await ctx.defer(ephemeral=True)

        # Get gold purchases
        async with db.Database.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM guild_specific_families WHERE purchased_by = $1",
                ctx.user.id,
            )
            _, this_guild_active = await u.get_guild_id_and_gold(self.bot, ctx)
        if not rows:
            return await ctx.send(
                ctx._("You haven't purchased any instances of MarriageBot Gold!"),
                ephemeral=True,
            )
        if this_guild_active:
            return await ctx.send(
                ctx._("MarriageBot Gold has already been purchased for this server!"),
                ephemeral=True,
            )

        async def get_guild_name(guild_id: int) -> str:
            guild = self.bot.get_guild(guild_id)
            if guild:
                return guild.name
            try:
                guild = await n.Guild.fetch(self.state, guild_id)
                return guild.name
            except Exception:
                return f"Guild[{guild_id}]"

        available_guilds = [
            ((await get_guild_name(row["guild_id"])), row["guild_id"],)
            for row in rows if row["guild_id"] != ctx.guild.id
        ]
        available_guilds.sort(
            key=lambda x: (x[0].lower() if not x[0].startswith("Guild[") else "zzzz" + x[0]),
        )  # Sort guilds alphabetically, other than `Guild[xxx]`, which go last.

        # Ask the user where they want to transfer from
        return await ctx.send(
            ctx._(
                "I'm going to transfer your MarriageBot Gold purchase into **this server**. "
                "Which server would you like to transfer your Gold purchase *from*?"
            ),
            components=[
                n.ActionRow([
                    n.StringSelectMenu(
                        custom_id=f"TRANSFER_GOLD_SELECT {ctx.user.id}",
                        placeholder=ctx._("Select a server"),
                        options=[
                            n.SelectOption(
                                label=g[0],
                                value=str(g[1]),
                            )
                            for g in available_guilds
                        ],
                        min_values=1,
                        max_values=1,
                    )
                ])
            ],
            ephemeral=True,
        )

    @client.event.filtered_component(r"^TRANSFER_GOLD_SELECT (\d+)$")
    async def on_transfer_gold_select(self, ctx: n.Interaction[n.MessageComponentData]) -> None:
        """
        Pinged when a user selects a server to transfer their MarriageBot Gold purchase from.
        """

        # Make sure the right user is using the dropdown
        if not ctx.guild:
            return  # Silently fail
        if (ctx.custom_id or "").split(" ")[1] != str(ctx.user.id):
            return await ctx.send(
                ctx._("You cannot transfer someone else's MarriageBot Gold purchase!"),
                ephemeral=True,
            )

        await ctx.defer_update()

        # Perform our logistics
        selected = ctx.data.values[0]
        guild_id = int(selected.value)
        async with db.Database.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM guild_specific_families WHERE purchased_by = $1 AND guild_id = $2",
                ctx.user.id, guild_id,
            )
            if row is None:
                return await ctx.send(
                    (
                        ctx._(
                            "You didn't purchase the Gold subscription that's active in "
                            "**{guild_name}**"
                        )
                        .format(guild_name=selected.label)
                    ),
                    ephemeral=True,
                )

            try:
                await conn.execute(
                    """
                    UPDATE
                        guild_specific_families
                    SET
                        guild_id = $1
                    WHERE
                        guild_id = $2
                        AND purchased_by = $3
                    """,
                    ctx.guild.id,
                    guild_id,
                    ctx.user.id,
                )
            except Exception:
                return await ctx.send(
                    ctx._("There was an error transferring your MarriageBot Gold purchase."),
                    ephemeral=True,
                )

            await conn.execute(
                """
                UPDATE
                    guild_settings
                SET
                    guild_specific_families = FALSE
                WHERE
                    guild_id = $1
                """,
                guild_id,
            )

        await ctx.edit_original(
            content=ctx._(
                "Your MarriageBot Gold purchase has been transferred to this server! You can now "
                "run the {command_ping} command to activate it here :3"
            ).format(command_ping=self.guild_specific_families_guild_settings.get_mention()),
            components=None,
        )

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

        if self.bot.config.gold:
            return await ctx.send(ctx._(
                "This command cannot be run on the Gold version of MarriageBot. "
                "The regular version of MarriageBot now allows you to toggle between "
                "guild-specific families and global families.\n\nTo use this command, please "
                "change over to the regular version of MarriageBot and run this command."
            ))

        async with db.Database.acquire() as conn:
            gold_enabled = await conn.fetchval(
                """
                SELECT TRUE FROM guild_specific_families WHERE guild_id = $1
                """,
                ctx.guild.id,
            )
            gold_enabled = bool(gold_enabled)

        if not gold_enabled:
            components = u.get_upsell_components(ctx, gold=True)
            return await ctx.send(
                ctx._(
                    "You can only switch to guild-specific families (and thus use the `/force` "
                    "and `/incest` commands, enable polygamy for everyone in your server, and "
                    "increase your child count) after you have purchased MarriageBot Gold."
                ),
                components=components
            )

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
                ).format(guild_specific_command=command.mention)
            )
        else:
            await ctx.send(
                ctx._(
                    "Guild-specific families are now **disabled** in this guild. You are now "
                    "switched back to the global MarriageBot tree.\n\nYou can switch back to your "
                    "guild-specific tree by using the {guild_specific_command} command :3"
                ).format(guild_specific_command=command.mention)
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
