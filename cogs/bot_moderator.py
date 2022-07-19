from __future__ import annotations

import discord
from discord.ext import commands, vbu

from cogs import utils


class BotModerator(vbu.Cog[utils.types.Bot], command_attrs={'hidden': True}):

    @commands.command()
    @vbu.checks.is_bot_support()
    @commands.bot_has_permissions(send_messages=True)
    async def runstartupmethod(self, ctx: vbu.Context):
        """
        Runs the bot startup method, recaching everything of interest.
        """

        async with ctx.typing():
            await self.bot.startup()
        await ctx.send("Done.")

    @commands.command()
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

    @commands.command()
    @vbu.checks.is_bot_support()
    @commands.bot_has_permissions(send_messages=True)
    async def copyfamilytoguild(
            self,
            ctx: vbu.Context,
            user: vbu.converters.UserID,
            guild_id: int):
        """
        Copies a family's span to a given guild ID for server
        specific families.
        """

        await self.copy_family(ctx, user, guild_id, False)

    async def copy_family(
            self,
            ctx: vbu.Context,
            user_id: int,
            guild_id: int,
            delete_members: bool):
        """
        Copy a family to a given Gold guild.
        """

        if guild_id == 0:
            return await ctx.send("No.")

        # Get their current family
        tree = utils.FamilyTreeMember.get(user_id, guild_id=0)
        users = list(tree.span(expand_upwards=True, add_parent=True))
        await ctx.channel.trigger_typing()

        # Database it to the new guild
        db = await self.bot.database.get_connection()

        # Delete current guild data
        if delete_members:
            await db("DELETE FROM marriages WHERE guild_id=$1", guild_id)
            await db("DELETE FROM parents WHERE guild_id=$1", guild_id)

        # Generate new data to copy
        parents = ((i.id, i._parent, guild_id) for i in users if i._parent)
        partners = ((i.id, i._partner, guild_id) for i in users if i._partner)

        # Push to db
        assert db.conn
        try:
            await db.conn.copy_records_to_table(
                'parents',
                columns=['child_id', 'parent_id', 'guild_id'],
                records=parents,
            )
            await db.conn.copy_records_to_table(
                'marriages',
                columns=['user_id', 'partner_id', 'guild_id'],
                records=partners,
            )
        except Exception:
            return await ctx.send("I encountered an error copying that family over.")

        # Send to user
        await db.disconnect()
        await ctx.send((
            f"Copied over `{len(users)}` users. "
            "Be sure to run the `runstartupmethod` command"
        ))

    @commands.command()
    @vbu.checks.is_bot_support()
    @commands.bot_has_permissions(send_messages=True)
    async def addserverspecific(
            self,
            ctx: vbu.Context,
            guild_id: int,
            user_id: vbu.converters.UserID):
        """
        Adds a guild to the MarriageBot Gold whitelist.
        """

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
                guild_id, user_id,
            )
        await ctx.send("Done.")

    @commands.command()
    @vbu.checks.is_bot_support()
    @commands.bot_has_permissions(send_messages=True)
    async def removeserverspecific(
            self,
            ctx: vbu.Context,
            guild_id: int):
        """
        Remove a guild from the MarriageBot Gold whitelist.
        """

        async with vbu.Database() as db:
            await db(
                """
                DELETE FROM
                    guild_specific_families
                WHERE
                    guild_id = $1
                """,
                guild_id,
            )
        await ctx.send("Done.")

    @commands.command(aliases=['getgoldpurchase'])
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
            return await ctx.send("That user has purchased no instances of MarriageBot Gold.")

        # Spit out their guild IDs
        format_text = (
            "<@{user_id}> has purchased {0} "
            "{0:plural,instance,instances} of MarriageBot Gold:\n"
        )
        text = vbu.format(format_text, len(rows))
        text += "\n".join([f"\N{BULLET} `{i['guild_id']}`" for i in rows])
        return await ctx.send(text, allowed_mentions=discord.AllowedMentions.none())


def setup(bot: utils.types.Bot):
    x = BotModerator(bot)
    bot.add_cog(x)
