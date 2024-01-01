from __future__ import annotations
from typing import Optional

import discord
from discord.ext import commands, vbu

from cogs import utils


class BotModerator(vbu.Cog[utils.types.Bot]):

    @commands.command(
        application_command_meta=commands.ApplicationCommandMeta(
            guild_ids=[
                208895639164026880,
            ]
        )
    )
    @vbu.checks.is_bot_support()
    @commands.bot_has_permissions(send_messages=True)
    async def runstartupmethod(self, ctx: vbu.Context):
        """
        Runs the bot startup method, recaching everything of interest.
        """

        async with ctx.typing():
            await self.bot.startup()
        await ctx.send("Done.")

    @commands.command(
        application_command_meta=commands.ApplicationCommandMeta(
            guild_ids=[
                208895639164026880,
            ],
            options=[
                discord.ApplicationCommandOption(
                    name="user",
                    description="The user ID to copy",
                    required=True,
                    type=discord.ApplicationCommandOptionType.user,
                ),
                discord.ApplicationCommandOption(
                    name="guild_id",
                    description="The guild ID to copy to",
                    required=True,
                    type=discord.ApplicationCommandOptionType.integer,
                ),
            ],
        ),
    )
    @vbu.checks.is_bot_support()
    @commands.bot_has_permissions(send_messages=True)
    async def copyfamilytoguildwithdelete(
            self,
            ctx: vbu.Context,
            user: vbu.converters.UserID,
            guild_id: int):
        """
        Copies a family's span to a given guild ID for server
        specific families.
        """

        await self.copy_family(ctx, user, guild_id, True)

    @commands.command(
        application_command_meta=commands.ApplicationCommandMeta(
            guild_ids=[
                208895639164026880,
            ],
            options=[
                discord.ApplicationCommandOption(
                    name="user",
                    description="The user ID to copy",
                    required=True,
                    type=discord.ApplicationCommandOptionType.user,
                ),
                discord.ApplicationCommandOption(
                    name="guild_id",
                    description="The guild ID to copy to",
                    required=True,
                    type=discord.ApplicationCommandOptionType.string,
                ),
            ],
        ),
    )
    @vbu.checks.is_bot_support()
    @commands.bot_has_permissions(send_messages=True)
    async def copyfamilytoguild(
            self,
            ctx: vbu.SlashContext,
            user: vbu.converters.UserID,
            guild_id: str):
        """
        Copies a family's span to a given guild ID for server
        specific families.
        """

        if not guild_id.isdigit():
            return await ctx.interaction.response.send_message("That is not a valid guild ID.")
        await self.copy_family(ctx, user, int(guild_id), False)

    async def copy_family(
            self,
            ctx: vbu.SlashContext,
            user_id: int,
            guild_id: int,
            delete_members: bool):
        """
        Copy a family to a given Gold guild.
        """

        if guild_id == 0:
            return await ctx.interaction.response.send_message("No.")

        # Get their current family
        tree = utils.FamilyTreeMember.get(user_id, guild_id=0)
        users = list(tree.span(expand_upwards=True, add_parent=True))
        await ctx.interaction.response.defer()

        # Database it to the new guild
        db = await self.bot.database.get_connection()

        # Delete current guild data
        if delete_members:
            await db("DELETE FROM marriages WHERE guild_id = $1", guild_id)
            await db("DELETE FROM parents WHERE guild_id = $1", guild_id)

        # Generate new data to copy
        parents = [(i.id, i._parent, guild_id) for i in users if i._parent]
        partners = []
        for i in users:
            partners.extend((*sorted([i.id, p.id]), guild_id) for p in i.partners)
        partners = list(set(partners))

        # Push to db
        assert db.conn
        try:
            await db.executemany(
                """
                INSERT INTO
                    parents
                    (
                        child_id,
                        parent_id,
                        guild_id
                    )
                VALUES
                    (
                        $1,
                        $2,
                        $3
                    )
                ON CONFLICT
                    (child_id, guild_id)
                DO NOTHING
                """,
                *parents,
            )
            await db.executemany(
                """
                INSERT INTO
                    marriages
                    (
                        user_id,
                        partner_id,
                        guild_id
                    )
                VALUES
                    (
                        $1,
                        $2,
                        $3
                    )
                ON CONFLICT
                    (user_id, partner_id, guild_id)
                DO NOTHING
                """,
                *partners,
            )
        except Exception as e:
            return await ctx.send(
                f"I encountered an error copying that family over - `{e}`."
            )

        # Send to user
        await db.disconnect()
        await ctx.send((
            f"Copied over `{len(users)}` users. "
            "Be sure to run the `runstartupmethod` command"
        ))

    @commands.command(
        application_command_meta=commands.ApplicationCommandMeta(
            guild_ids=[
                208895639164026880,
            ],
            options=[
                discord.ApplicationCommandOption(
                    name="guild_id",
                    description="The guild ID to add.",
                    required=True,
                    type=discord.ApplicationCommandOptionType.string,
                ),
                discord.ApplicationCommandOption(
                    name="user_id",
                    description="The user to assign the guild to.",
                    required=True,
                    type=discord.ApplicationCommandOptionType.user,
                ),
            ],
        ),
    )
    @vbu.checks.is_bot_support()
    @commands.bot_has_permissions(send_messages=True)
    async def addserverspecific(
            self,
            ctx: vbu.SlashContext,
            guild_id: str,
            user_id: vbu.converters.UserID):
        """
        Adds a guild to the MarriageBot Gold whitelist.
        """

        if not guild_id.isdigit():
            return await ctx.interaction.response.send_message("That is not a valid guild ID.")
        async with vbu.Database() as db:
            await db(
                """
                INSERT INTO
                    guild_specific_families
                    (
                        guild_id,
                        purchased_by
                    )
                VALUES
                    (
                        $1,
                        $2
                    )
                ON CONFLICT (guild_id)
                DO UPDATE
                SET
                    purchased_by = excluded.purchased_by
                """,
                int(guild_id), user_id,
            )
        await ctx.send("Done.")

    @commands.command(
        application_command_meta=commands.ApplicationCommandMeta(
            guild_ids=[
                208895639164026880,
            ],
            options=[
                discord.ApplicationCommandOption(
                    name="guild_id",
                    description="The guild ID to remove.",
                    required=True,
                    type=discord.ApplicationCommandOptionType.string,
                ),
            ],
        ),
    )
    @vbu.checks.is_bot_support()
    @commands.bot_has_permissions(send_messages=True)
    async def removeserverspecific(
            self,
            ctx: vbu.SlashContext,
            guild_id: str):
        """
        Remove a guild from the MarriageBot Gold whitelist.
        """

        if not guild_id.isdigit():
            return await ctx.interaction.response.send_message("That is not a valid guild ID.")
        async with vbu.Database() as db:
            await db(
                """
                DELETE FROM
                    guild_specific_families
                WHERE
                    guild_id = $1
                """,
                int(guild_id),
            )
        await ctx.send("Done.")
    
    @commands.command(
        application_command_meta=commands.ApplicationCommandMeta(
            guild_ids=[
                208895639164026880,
            ],
            options=[
                discord.ApplicationCommandOption(
                    name="old_guild_id",
                    description="The guild ID to remove.",
                    required=True,
                    type=discord.ApplicationCommandOptionType.string,
                ),
                discord.ApplicationCommandOption(
                    name="new_guild_id",
                    description="The guild ID to add.",
                    required=True,
                    type=discord.ApplicationCommandOptionType.string,
                ),
                discord.ApplicationCommandOption(
                    name="user_id",
                    description="The user to assign the guild to.",
                    required=True,
                    type=discord.ApplicationCommandOptionType.user,
                ),
            ],
        ),
    )
    @vbu.checks.is_bot_support()
    @commands.bot_has_permissions(send_messages=True)
    async def transferserverspecific(
                self,
                ctx: vbu.SlashContext,
                old_guild_id: str,
                new_guild_id: str,
                user_id: vbu.converters.UserID):
        """
        Transfers a MarriageBot Gold purchase to another server.
        """

        if not old_guild_id.isdigit() or not new_guild_id.isdigit():
            return await ctx.interaction.response.send_message("That is not a valid guild ID.")
        
        async with vbu.Database() as db:
            await db(
                """
                DELETE FROM
                    guild_specific_families
                WHERE
                    guild_id = $1
                """,
                int(old_guild_id),
            )

            await db(
                """
                INSERT INTO
                    guild_specific_families
                    (
                        guild_id,
                        purchased_by
                    )
                VALUES
                    (
                        $1,
                        $2
                    )
                ON CONFLICT (guild_id)
                DO UPDATE
                SET
                    purchased_by = excluded.purchased_by
                """,
                int(new_guild_id), user_id,
            )

        await ctx.send("Done.")

    @commands.command(
        aliases=['getgoldpurchase'],
        application_command_meta=commands.ApplicationCommandMeta(
            guild_ids=[
                208895639164026880,
            ],
            options=[
                discord.ApplicationCommandOption(
                    name="user_id",
                    description="The user to check.",
                    required=True,
                    type=discord.ApplicationCommandOptionType.user,
                ),
            ],
        ),
    )
    @vbu.checks.is_bot_support()
    @commands.bot_has_permissions(send_messages=True)
    async def getgoldpurchases(
            self,
            ctx: vbu.Context,
            user_id: vbu.converters.UserID):
        """
        Remove a guild from the MarriageBot Gold whitelist.
        """

        # Get the rows
        async with vbu.Database() as db:
            rows = await db(
                """
                SELECT
                    guild_id
                FROM
                    guild_specific_families
                WHERE
                    purchased_by = $1
                """,
                user_id,
            )

        # They haven't purchased anything
        if not rows:
            return await ctx.send(
                (
                    "That user has purchased no "
                    "instances of MarriageBot Gold."
                )
            )

        # Spit out their guild IDs
        format_text = (
            "<@{1}> has purchased {0} "
            "{0:plural,instance,instances} of MarriageBot Gold:\n"
        )
        text = vbu.format(format_text, len(rows), user_id)
        text += "\n".join([f"\N{BULLET} `{i['guild_id']}`" for i in rows])
        return await ctx.send(
            text,
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @commands.command(
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="guild_id",
                    description="The ID of the guild to reset.",
                    type=discord.ApplicationCommandOptionType.string,
                    required=False
                ),
            ],
            guild_ids=[
                208895639164026880,
            ],
        ),
    )
    @vbu.checks.is_bot_support()
    @commands.bot_has_permissions(send_messages=True)
    async def forcereset(
            self,
            ctx: vbu.Context,
            guild_id: Optional[str] = None):
        """Completely resets a server-specific tree given a guild ID."""

        if guild_id and not guild_id.isdigit():
            return await ctx.send("No guild found.")
        await self.reset_family(ctx, int(guild_id) if isinstance(guild_id, int) else None)


    async def reset_family(
            self,
            ctx: vbu.Context,
            guild_id: Optional[int]):
        """Resets a family tree for a guild"""

        if guild_id == 0:
            return await ctx.send("Absolutely not.")

        try:
            guild_id = guild_id or ctx.guild.id
        except AttributeError:
            # I'm assuming if it's run in DMs `ctx.guild` would be None
            return await ctx.send("No guild found.")

        assert guild_id  # Let's not erase global tree <3

        # Update database
        async with vbu.Database() as db:
            await db("DELETE FROM parents WHERE guild_id = $1", guild_id)
            await db("DELETE FROM marriages WHERE guild_id = $1", guild_id)

        await ctx.send("Reset tree. Run the `runstartupmethod` command.")


def setup(bot: utils.types.Bot):
    x = BotModerator(bot)
    bot.add_cog(x)
