from datetime import datetime as dt

import asyncpg
import discord
from discord.ext import commands
import voxelbotutils as utils

from cogs import utils as localutils


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


class ServerSpecific(utils.Cog):

    @utils.Cog.listener()
    async def on_guild_join(self, guild:discord.Guild):
        """
        Looks for when the bot is added to a guild, leaving if it's not whitelisted.
        """

        if not self.bot.config['is_server_specific']:
            return
        async with self.bot.database() as db:
            data = await db("SELECT guild_id FROM guild_specific_families WHERE guild_id=$1", guild.id)
        if data:
            return
        self.logger.warn(f"Automatically left guild {guild.name} ({guild.id}) for non-subscription")
        await guild.leave()

    @utils.command(add_slash_command=False)
    @utils.cooldown.cooldown(1, 5, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    @utils.checks.is_config_set('command_data', 'stats_command_enabled')
    async def perks(self, ctx:utils.Context):
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
        e.add_field(name='Normal Users', value="Gives you access to:\n* " + '\n* '.join(normal_users), inline=False)
        e.add_field(name=f'Voting ({ctx.prefix}vote)', value="Gives you access to:\n* " + '\n* '.join(voting_perks), inline=False)
        e.add_field(name=f'T1 Subscriber ({ctx.prefix}donate)', value="Gives you access to:\n* " + '\n* '.join(t1_donate_perks), inline=False)
        e.add_field(name=f'T2 Subscriber ({ctx.prefix}donate)', value="Gives you access to:\n* " + '\n* '.join(t2_donate_perks), inline=False)
        e.add_field(name=f'T3 Subscriber ({ctx.prefix}donate)', value="Gives you access to:\n* " + '\n* '.join(t3_donate_perks), inline=False)
        e.add_field(name=f'MarriageBot Gold ({ctx.prefix}gold)', value="Gives you access to:\n* " + '\n* '.join(gold_perks), inline=False)
        await ctx.send(embed=e)

    @utils.command(hidden=True)
    @utils.cooldown.no_raise_cooldown(1, 3, commands.BucketType.user)
    @localutils.checks.is_server_specific_bot_moderator()
    @localutils.checks.guild_is_server_specific()
    @commands.bot_has_permissions(send_messages=True)
    async def allowincest(self, ctx:utils.Context):
        """
        Toggles allowing incest on your guild.
        """

        async with self.bot.database() as db:
            await db(
                """INSERT INTO guild_settings (guild_id, allow_incest) VALUES ($1, $2) ON CONFLICT (guild_id)
                DO UPDATE SET allow_incest=excluded.allow_incest""",
                ctx.guild.id, True,
            )
        self.bot.guild_settings[ctx.guild.id]['allow_incest'] = True
        await ctx.send("Incest is now **ALLOWED** on your guild.")

    @utils.command(hidden=True)
    @utils.cooldown.no_raise_cooldown(1, 3, commands.BucketType.user)
    @localutils.checks.is_server_specific_bot_moderator()
    @localutils.checks.guild_is_server_specific()
    @commands.bot_has_permissions(send_messages=True)
    async def disallowincest(self, ctx:utils.Context):
        """
        Toggles allowing incest on your guild.
        """

        async with self.bot.database() as db:
            await db(
                """INSERT INTO guild_settings (guild_id, allow_incest) VALUES ($1, $2) ON CONFLICT (guild_id)
                DO UPDATE SET allow_incest=excluded.allow_incest""",
                ctx.guild.id, False,
            )
        self.bot.guild_settings[ctx.guild.id]['allow_incest'] = False
        await ctx.send("Incest is now **DISALLOWED** on your guild.")

    @utils.group(add_slash_command=False)
    @utils.cooldown.no_raise_cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def incest(self, ctx:utils.Context):
        """
        Toggles allowing incest on your guild.
        """

        if not self.bot.config['is_server_specific']:
            return await ctx.send(f"Incest is only allowed in the server-specific version of MarriageBot - see `{ctx.clean_prefix}gold` for more information.")
        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @incest.command(name="allow", aliases=['enable', 'on', 'start'], add_slash_command=False)
    @utils.cooldown.no_raise_cooldown(1, 3, commands.BucketType.user)
    @localutils.checks.is_server_specific_bot_moderator()
    @localutils.checks.guild_is_server_specific()
    @commands.bot_has_permissions(send_messages=True)
    async def incest_allow(self, ctx:utils.Context):
        """
        Toggles allowing incest on your guild.
        """

        async with self.bot.database() as db:
            await db(
                """INSERT INTO guild_settings (guild_id, allow_incest) VALUES ($1, $2) ON CONFLICT (guild_id)
                DO UPDATE SET allow_incest=excluded.allow_incest""",
                ctx.guild.id, True,
            )
        self.bot.guild_settings[ctx.guild.id]['allow_incest'] = True
        await ctx.send("Incest is now **ALLOWED** on your guild.")

    @incest.command(name="disallow", aliases=['disable', 'off', 'stop'], add_slash_command=False)
    @utils.cooldown.no_raise_cooldown(1, 3, commands.BucketType.user)
    @localutils.checks.is_server_specific_bot_moderator()
    @localutils.checks.guild_is_server_specific()
    @commands.bot_has_permissions(send_messages=True)
    async def incest_disallow(self, ctx:utils.Context):
        """
        Toggles allowing incest on your guild.
        """

        async with self.bot.database() as db:
            await db(
                """INSERT INTO guild_settings (guild_id, allow_incest) VALUES ($1, $2) ON CONFLICT (guild_id)
                DO UPDATE SET allow_incest=excluded.allow_incest""",
                ctx.guild.id, False,
            )
        self.bot.guild_settings[ctx.guild.id]['allow_incest'] = False
        await ctx.send("Incest is now **DISALLOWED** on your guild.")

    @utils.command(aliases=['ssf'], add_slash_command=False)
    @utils.cooldown.no_raise_cooldown(1, 3, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def gold(self, ctx:utils.Context):
        """
        Gives you the information about server specific families and MarriageBot Gold.
        """

        try:
            await ctx.author.send(MARRIAGEBOT_GOLD_INFORMATION.strip())
            await ctx.send("Sent you a DM!")
        except discord.Forbidden:
            await ctx.send("I couldn't send you a DM :c")

    @utils.command(add_slash_command=False)
    @localutils.checks.is_server_specific_bot_moderator()
    @commands.bot_has_permissions(send_messages=True)
    async def forcemarry(self, ctx:utils.Context, usera:utils.converters.UserID, userb:utils.converters.UserID=None):
        """
        Marries the two specified users.
        """

        # Correct params
        if userb is None:
            usera, userb = ctx.author.id, usera
        if usera == userb:
            return await ctx.send("You can't marry yourself.")

        # Get users
        family_guild_id = localutils.get_family_guild_id(ctx)
        usera_tree, userb_tree = localutils.FamilyTreeMember.get_multiple(usera, userb, guild_id=family_guild_id)

        # See if they have partners
        if usera_tree._partner is not None:
            user_name = await localutils.DiscordNameManager.fetch_name_by_id(self.bot, usera)
            return await ctx.send(f"**{user_name}** already has a partner.", allowed_mentions=discord.AllowedMentions.none())
        if userb_tree._partner is not None:
            user_name = await localutils.DiscordNameManager.fetch_name_by_id(self.bot, userb)
            return await ctx.send(f"**{user_name}** already has a partner.", allowed_mentions=discord.AllowedMentions.none())

        # Update database
        async with self.bot.database() as db:
            try:
                await db.start_transaction()
                await db(
                    "INSERT INTO marriages (user_id, partner_id, guild_id, timestamp) VALUES ($1, $2, $3, $4), ($2, $1, $3, $4)",
                    usera_tree.id, userb_tree.id, family_guild_id, dt.utcnow(),
                )
                await db.commit_transaction()
            except asyncpg.UniqueViolationError:
                return await ctx.send("I ran into an error saving your family data.")
        usera_name = await localutils.DiscordNameManager.fetch_name_by_id(self.bot, usera_tree.id)
        userb_name = await localutils.DiscordNameManager.fetch_name_by_id(self.bot, userb_tree.id)
        await ctx.send(f"Married **{usera_name}** and **{userb_name}**.", allowed_mentions=discord.AllowedMentions.none())

        # Update cache
        usera_tree._partner = userb
        userb_tree._partner = usera
        async with self.bot.redis() as re:
            await re.publish('TreeMemberUpdate', usera_tree.to_json())
            await re.publish('TreeMemberUpdate', userb_tree.to_json())

    @utils.command(add_slash_command=False)
    @localutils.checks.is_server_specific_bot_moderator()
    @commands.bot_has_permissions(send_messages=True)
    async def forcedivorce(self, ctx:utils.Context, usera:utils.converters.UserID):
        """
        Divorces a user from their spouse.
        """

        # Get user
        family_guild_id = localutils.get_family_guild_id(ctx)
        usera_tree = localutils.FamilyTreeMember.get(usera, guild_id=family_guild_id)
        usera_name = await localutils.DiscordNameManager.fetch_name_by_id(self.bot, usera)
        if not usera_tree.partner:
            return await ctx.send(f"**{usera_name}** isn't even married .-.", allowed_mentions=discord.AllowedMentions.none())

        # Update database
        async with self.bot.database() as db:
            await db(
                """DELETE FROM marriages WHERE (user_id=$1 OR partner_id=$1) AND guild_id=$2""",
                usera, family_guild_id,
            )

        # Update cache
        usera_tree.partner._partner = None
        userb_tree = usera_tree.partner
        usera_tree._partner = None
        async with self.bot.redis() as re:
            await re.publish('TreeMemberUpdate', usera_tree.to_json())
            await re.publish('TreeMemberUpdate', userb_tree.to_json())
        await ctx.send("Consider it done.")

    @utils.command(add_slash_command=False)
    @localutils.checks.is_server_specific_bot_moderator()
    @commands.bot_has_permissions(send_messages=True)
    async def forceadopt(self, ctx:utils.Context, parent:utils.converters.UserID, child:utils.converters.UserID=None):
        """
        Adds the child to the specified parent.
        """

        # Correct params
        if child is None:
            parent_id, child_id = ctx.author.id, parent
        else:
            parent_id, child_id = parent, child

        # Check users
        family_guild_id = localutils.get_family_guild_id(ctx)
        parent_tree, child_tree = localutils.FamilyTreeMember.get_multiple(parent_id, child_id, guild_id=family_guild_id)
        child_name = await localutils.DiscordNameManager.fetch_name_by_id(self.bot, child_id)
        if child_tree.parent:
            return await ctx.send(f"**{child_name}** already has a parent.", allowed_mentions=discord.AllowedMentions.none())
        parent_name = await localutils.DiscordNameManager.fetch_name_by_id(self.bot, parent_tree.id)

        # Update database
        async with self.bot.database() as db:
            try:
                await db(
                    """INSERT INTO parents (parent_id, child_id, guild_id, timestamp) VALUES ($1, $2, $3, $4)""",
                    parent_id, child_id, family_guild_id, dt.utcnow(),
                )
            except asyncpg.UniqueViolationError:
                return await ctx.send("I ran into an error saving your family data.")

        # Update cache
        parent_tree._children.append(child_id)
        child_tree._parent = parent
        async with self.bot.redis() as re:
            await re.publish('TreeMemberUpdate', parent_tree.to_json())
            await re.publish('TreeMemberUpdate', child_tree.to_json())
        await ctx.send(f"Added **{child_name}** to **{parent_name}**'s children list.")

    @utils.command(aliases=['forceeman'], add_slash_command=False)
    @localutils.checks.is_server_specific_bot_moderator()
    @commands.bot_has_permissions(send_messages=True)
    async def forceemancipate(self, ctx:utils.Context, child:utils.converters.UserID):
        """
        Force emancipates a child.
        """

        # Run checks
        family_guild_id = localutils.get_family_guild_id(ctx)
        child_tree = localutils.FamilyTreeMember.get(child, family_guild_id)
        child_name = await localutils.DiscordNameManager.fetch_name_by_id(self.bot, child)
        if not child_tree._parent:
            return await ctx.send(f"**{child_name}** doesn't even have a parent .-.")

        # Update database
        async with self.bot.database() as db:
            await db(
                """DELETE FROM parents WHERE child_id=$1 AND guild_id=$2""",
                child, family_guild_id,
            )

        # Update cache
        try:
            child_tree.parent._children.remove(child)
        except ValueError:
            pass
        parent = child_tree.parent
        child_tree._parent = None
        async with self.bot.redis() as re:
            await re.publish('TreeMemberUpdate', child_tree.to_json())
            await re.publish('TreeMemberUpdate', parent.to_json())
        await ctx.send("Consider it done.")


def setup(bot:utils.Bot):
    x = ServerSpecific(bot)
    bot.add_cog(x)
