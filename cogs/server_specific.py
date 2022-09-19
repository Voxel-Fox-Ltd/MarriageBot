from __future__ import annotations

from datetime import datetime as dt
from typing import Optional

import asyncpg
import discord
from discord.ext import commands, vbu

from cogs import utils


MARRIAGEBOT_GOLD_INFORMATION = """
**MarriageBot Gold** is, put simply, the premium version of MarriageBot. It gives you a range of features that aren't present in the normal version of MarriageBot, which can help making your families even better than before.

**Server Specific Families**
> This allows you to keep families registered to your own guild. No more will you be trying to marry someone to find out they have a partner you've never met 4 servers away - all family members will be kept right on your server.
**5s Tree Command Cooldown**
> The tree command cooldown is reduced _massively_ to just 5s per command call, instead of the 60s that the regular MarriageBot has.
**"force" Commands**
> Users with a role named "MarriageBot Moderator" will be able to run commands like `forceadopt` and `forcemarry` in order to construct trees exactly how you want them.
**Configurable Max Family Members**
> Via the MarriageBot website, you're able to set the maximum number of members in a family to a number up to 2,000 people, putting it far above the amount offered normally.
**Configurable Max Children Amount**
> Stuck with only 5 children? Using the MarriageBot website, you're able to set the maximum number of children that a given role can have, allowing you to tier your users.
**Togglable Incest**
> You love your family? With Gold you're able to show them... a lot _more_ love.

MarriageBot Gold is a one-time purchase available per server on the MarriageBot website (<https://marriagebot.xyz/guilds>).
Please feel free to direct any questions to the team at `m!support`.
""".strip()


class ServerSpecific(vbu.Cog[utils.types.Bot]):

    @vbu.Cog.listener()
    async def on_guild_join(
            self,
            guild: discord.Guild):
        """
        Looks for when the bot is added to a guild, leaving if it's not whitelisted.
        """

        # See if we're server specific
        if not self.bot.config['is_server_specific']:
            return

        # If we are, see if this guild is valid
        async with vbu.Database() as db:
            data = await db(
                """
                SELECT
                    guild_id
                FROM
                    guild_specific_families
                WHERE
                    guild_id = $1
                """,
                guild.id,
            )

        # We valid
        if data:
            return

        # Leave invalid server
        self.logger.warn(f"Automatically left guild {guild.name} ({guild.id}) for non-subscription")
        await guild.leave()

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    @vbu.checks.is_config_set("bot_info", "links", "Donate")
    async def perks(self, ctx: vbu.Context):
        """
        Shows you the perks associated with different support tiers.
        """

        # Normies
        normal_users = [
            "60s tree cooldown",
            "5 children",
        ]

        # Perks for voting
        voting_perks = [
            "30s tree cooldown",
            "5 children",
        ]

        # The Nitro perks would go here but I want to keep them mostly undocumented

        # Perks for $1 Patrons
        t1_donate_perks = [
            "15s tree cooldown",
            "10 children",
            "`disownall` command (disowns all of your children at once)",
        ]

        # $3 Patrons
        t2_donate_perks = [
            "15s tree cooldown",
            "15 children",
            "`disownall` command (disowns all of your children at once)",
            "`bloodtree` command (shows all relations, not just blood relatives)",
        ]

        # Perks for $5 Patrons
        t3_donate_perks = [
            "5s tree cooldown",
            "20 children",
            "`disownall` command (disowns all of your children at once)",
            "`bloodtree` command (shows all relations, not just blood relatives)",
        ]

        # Perks for MarriageBot Gold
        gold_perks = [
            "5s tree cooldown for all users",
            "Togglable incest",
            "Server specific families",
            "Access to the `forcemarry`, `forcedivorce`, and `forceemancipate` commands",
            f"Maximum 2000 family members (as opposed to the normal {self.bot.config['max_family_members']})",
            "Configurable maximum children per role",
        ]

        # Make embed
        e = discord.Embed()
        e.add_field(
            name='Normal Users',
            value="Gives you access to:\n* " + '\n* '.join(normal_users),
            inline=False,
        )
        e.add_field(
            name=f'Voting ({ctx.prefix}info - vote)',
            value="Gives you access to:\n* " + '\n* '.join(voting_perks),
            inline=False,
        )
        e.add_field(
            name=f'T1 Subscriber ({ctx.prefix}info - donate)',
            value="Gives you access to:\n* " + '\n* '.join(t1_donate_perks),
            inline=False,
        )
        e.add_field(
            name=f'T2 Subscriber ({ctx.prefix}info - donate)',
            value="Gives you access to:\n* " + '\n* '.join(t2_donate_perks),
            inline=False,
        )
        e.add_field(
            name=f'T3 Subscriber ({ctx.prefix}info - donate)',
            value="Gives you access to:\n* " + '\n* '.join(t3_donate_perks),
            inline=False,
        )
        e.add_field(
            name=f'MarriageBot Gold ({ctx.prefix}gold)',
            value=(
                (
                    "Gold is a seperate bot for your server, which "
                    "gives you perks such as:\n* "
                )  + '\n* '.join(gold_perks)
            ),
            inline=False,
        )
        await ctx.send(embed=e)

    @commands.group(
        application_command_meta=commands.ApplicationCommandMeta(),
    )
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def incest(
            self,
            ctx: vbu.Context):
        """
        Toggles allowing incest on your guild.
        """

        if not self.bot.config['is_server_specific']:
            return await ctx.send((
                f"Incest is only allowed in the server-specific version of MarriageBot - "
                f"see `{ctx.clean_prefix}gold` for more information."
            ))
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @incest.command(
        name="allow",
        aliases=['enable', 'on', 'start'],
        application_command_meta=commands.ApplicationCommandMeta(),
    )
    @commands.cooldown(1, 3, commands.BucketType.user)
    @utils.checks.is_server_specific_bot_moderator()
    @utils.checks.guild_is_server_specific()
    @commands.bot_has_permissions(send_messages=True)
    async def incest_allow(self, ctx: vbu.Context):
        """
        Toggles allowing incest on your guild.
        """

        assert ctx.guild
        async with vbu.Database() as db:
            await db(
                """
                INSERT INTO
                    guild_settings
                    (
                        guild_id,
                        allow_incest
                    )
                VALUES
                    (
                        $1,
                        $2
                    )
                ON CONFLICT
                    (guild_id)
                DO UPDATE SET
                    allow_incest = excluded.allow_incest
                """,
                ctx.guild.id, True,
            )
        self.bot.guild_settings[ctx.guild.id]['allow_incest'] = True
        await ctx.send("Incest is now **ALLOWED** on your guild.")

    @incest.command(
        name="disallow",
        aliases=['disable', 'off', 'stop'],
        application_command_meta=commands.ApplicationCommandMeta(),
    )
    @commands.cooldown(1, 3, commands.BucketType.user)
    @utils.checks.is_server_specific_bot_moderator()
    @utils.checks.guild_is_server_specific()
    @commands.bot_has_permissions(send_messages=True)
    async def incest_disallow(self, ctx: vbu.Context):
        """
        Toggles allowing incest on your guild.
        """

        assert ctx.guild
        async with vbu.Database() as db:
            await db(
                """
                INSERT INTO
                    guild_settings
                    (
                        guild_id,
                        allow_incest
                    )
                VALUES
                    (
                        $1,
                        $2
                    )
                ON CONFLICT
                    (guild_id)
                DO UPDATE SET
                    allow_incest = excluded.allow_incest
                """,
                ctx.guild.id, False,
            )
        self.bot.guild_settings[ctx.guild.id]['allow_incest'] = False
        await ctx.send("Incest is now **DISALLOWED** on your guild.")

    @commands.command(
        aliases=['ssf'],
        application_command_meta=commands.ApplicationCommandMeta(),
    )
    @commands.cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def gold(self, ctx: vbu.Context):
        """
        Gives you the information about server specific families and MarriageBot Gold.
        """

        try:
            await ctx.author.send(MARRIAGEBOT_GOLD_INFORMATION.strip())
            await ctx.send("Sent you a DM!")
        except discord.Forbidden:
            await ctx.send("I couldn't send you a DM :c")

    @commands.command(
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="user_a",
                    description="The first user you want to add to a marriage.",
                    type=discord.ApplicationCommandOptionType.user,
                ),
                discord.ApplicationCommandOption(
                    name="user_b",
                    description="The second user you want to add to a marriage.",
                    type=discord.ApplicationCommandOptionType.user,
                    required=False,
                ),
            ],
        ),
    )
    @utils.checks.is_server_specific_bot_moderator()
    @commands.bot_has_permissions(send_messages=True)
    async def forcemarry(
            self,
            ctx: vbu.Context,
            user_a: discord.User,
            user_b: Optional[discord.User] = None):
        """
        Marries the two specified users.
        """

        # Correct params
        if user_b is None:
            user_a, user_b = ctx.author, user_a  # type: ignore
        if user_a == user_b:
            return await ctx.send("You can't marry yourself.")

        # Get users
        family_guild_id = utils.get_family_guild_id(ctx)
        user_a_tree, user_b_tree = utils.FamilyTreeMember.get_multiple(
            user_a.id,
            user_b.id,
            guild_id=family_guild_id,
        )

        # Update database
        async with vbu.Database() as db:
            try:
                async with db.transaction() as trans:
                    await trans.call(
                        """
                        INSERT INTO
                            marriages
                            (
                                user_id,
                                partner_id,
                                guild_id,
                                timestamp
                            )
                        VALUES
                            (
                                $1,
                                $2,
                                $3,
                                $4
                            )
                        ON CONFLICT
                            (user_id, partner_id, guild_id)
                        DO NOTHING
                        """,
                        *sorted([user_a_tree.id, user_b_tree.id]), family_guild_id, dt.utcnow(),
                    )
            except asyncpg.UniqueViolationError:
                return await ctx.send("I ran into an error saving your family data.")
        user_a_name = await utils.DiscordNameManager.fetch_name_by_id(self.bot, user_a_tree.id)
        user_b_name = await utils.DiscordNameManager.fetch_name_by_id(self.bot, user_b_tree.id)
        await ctx.send(
            f"Married **{user_a_name}** and **{user_b_name}**.",
            allowed_mentions=discord.AllowedMentions.none(),
        )

        # Update cache
        user_a_tree.add_partner(user_b)
        user_b_tree.add_partner(user_a)
        async with vbu.Redis() as re:
            await re.publish("TreeMemberUpdate", user_a_tree.to_json())
            await re.publish("TreeMemberUpdate", user_b_tree.to_json())

    @commands.command(
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="user_a",
                    description="The user you want to force divorce.",
                    type=discord.ApplicationCommandOptionType.user,
                ),
                discord.ApplicationCommandOption(
                    name="user_b",
                    description="The other user you want to force divorce.",
                    type=discord.ApplicationCommandOptionType.user,
                ),
            ],
        ),
    )
    @utils.checks.is_server_specific_bot_moderator()
    @commands.bot_has_permissions(send_messages=True)
    async def forcedivorce(
            self,
            ctx: vbu.Context,
            user_a: discord.User,
            user_b: discord.User):
        """
        Divorces a user from their spouse.
        """

        # Get user
        family_guild_id = utils.get_family_guild_id(ctx)
        user_a_tree = utils.FamilyTreeMember.get(user_a.id, guild_id=family_guild_id)

        # Update database
        async with vbu.Database() as db:
            await db(
                """
                DELETE FROM
                    marriages
                WHERE
                    user_id = $1
                AND
                    partner_id = $2
                AND
                    guild_id = $3
                """,
                *sorted([user_a.id, user_b.id]), family_guild_id,
            )

        # Update cache
        user_b_tree = user_a_tree.remove_partner(user_b, return_added=True)
        user_b_tree.remove_partner(user_a)
        async with vbu.Redis() as re:
            await re.publish("TreeMemberUpdate", user_a_tree.to_json())
            await re.publish("TreeMemberUpdate", user_b_tree.to_json())
        await ctx.send("Consider it done.")

    @commands.command(
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="parent",
                    description="The parent in the relationship.",
                    type=discord.ApplicationCommandOptionType.user,
                ),
                discord.ApplicationCommandOption(
                    name="child",
                    description="The child in the relationship.",
                    type=discord.ApplicationCommandOptionType.user,
                ),
            ],
        ),
    )
    @utils.checks.is_server_specific_bot_moderator()
    @commands.bot_has_permissions(send_messages=True)
    async def forceadopt(
            self,
            ctx: vbu.Context,
            parent: discord.User,
            child: Optional[discord.User] = None):
        """
        Adds the child to the specified parent.
        """

        # Correct params
        if child is None:
            parent, child = ctx.author, parent  # type: ignore
        else:
            parent, child = parent, child

        # Check users
        family_guild_id = utils.get_family_guild_id(ctx)
        parent_tree, child_tree = utils.FamilyTreeMember.get_multiple(
            parent.id,
            child.id,
            guild_id=family_guild_id,
        )
        child_name = await utils.DiscordNameManager.fetch_name_by_id(self.bot, child.id)
        if child_tree.parent:
            return await ctx.send(
                f"**{child_name}** already has a parent.",
                allowed_mentions=discord.AllowedMentions.none(),
            )
        parent_name = await utils.DiscordNameManager.fetch_name_by_id(self.bot, parent_tree.id)

        # Update database
        async with vbu.Database() as db:
            try:
                await db(
                    """
                    INSERT INTO
                        parents
                        (
                            parent_id,
                            child_id,
                            guild_id,
                            timestamp
                        )
                    VALUES
                        (
                            $1,
                            $2,
                            $3,
                            $4
                        )
                    """,
                    parent.id, child.id, family_guild_id, dt.utcnow(),
                )
            except asyncpg.UniqueViolationError:
                return await ctx.send("I ran into an error saving your family data.")

        # Update cache
        parent_tree._children.append(child.id)
        child_tree._parent = parent.id
        async with vbu.Redis() as re:
            await re.publish('TreeMemberUpdate', parent_tree.to_json())
            await re.publish('TreeMemberUpdate', child_tree.to_json())
        await ctx.send(f"Added **{child_name}** to **{parent_name}**'s children list.")

    @commands.command(
        aliases=['forceeman'],
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="child",
                    description="The user you want to force emancipate.",
                    type=discord.ApplicationCommandOptionType.user,
                ),
            ],
        ),
    )
    @utils.checks.is_server_specific_bot_moderator()
    @commands.bot_has_permissions(send_messages=True)
    async def forceemancipate(
            self,
            ctx: vbu.Context,
            child: discord.User):
        """
        Force emancipates a child.
        """

        # See if the child has a parent
        family_guild_id = utils.get_family_guild_id(ctx)
        child_tree = utils.FamilyTreeMember.get(child.id, family_guild_id)
        child_name = await utils.DiscordNameManager.fetch_name_by_id(self.bot, child.id)
        if not child_tree.parent:
            return await ctx.send(f"**{child_name}** doesn't even have a parent .-.")

        # Update database
        async with vbu.Database() as db:
            await db(
                """
                DELETE FROM
                    parents
                WHERE
                    child_id = $1
                AND
                    guild_id = $2
                """,
                child.id, family_guild_id,
            )

        # Update cache
        try:
            child_tree.parent.remove_child(child.id)
        except ValueError:
            pass
        parent = child_tree.parent
        child_tree.parent = None
        async with vbu.Redis() as re:
            await re.publish("TreeMemberUpdate", child_tree.to_json())
            await re.publish("TreeMemberUpdate", parent.to_json())
        await ctx.send("Consider it done.")


def setup(bot: utils.types.Bot):
    x = ServerSpecific(bot)
    bot.add_cog(x)
