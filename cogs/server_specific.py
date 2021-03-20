import discord
from discord.ext import commands
import voxelbotutils

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


class ServerSpecific(voxelbotutils.Cog):

    @voxelbotutils.Cog.listener()
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

    @voxelbotutils.command(hidden=True)
    @localutils.checks.is_server_specific_bot_moderator()
    @localutils.checks.guild_is_server_specific()
    @commands.bot_has_permissions(send_messages=True)
    async def allowincest(self, ctx:voxelbotutils.Context):
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

    @voxelbotutils.command(hidden=True)
    @localutils.checks.is_server_specific_bot_moderator()
    @localutils.checks.guild_is_server_specific()
    @commands.bot_has_permissions(send_messages=True)
    async def disallowincest(self, ctx:voxelbotutils.Context):
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

    @voxelbotutils.group()
    @commands.bot_has_permissions(send_messages=True)
    async def incest(self, ctx:voxelbotutils.Context):
        """
        Toggles allowing incest on your guild.
        """

        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @incest.command(name="allow", aliases=['enable', 'on'])
    @localutils.checks.is_server_specific_bot_moderator()
    @localutils.checks.guild_is_server_specific()
    @commands.bot_has_permissions(send_messages=True)
    async def incest_allow(self, ctx:voxelbotutils.Context):
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

    @incest.command(name="disallow", aliases=['disable', 'off'])
    @localutils.checks.is_server_specific_bot_moderator()
    @localutils.checks.guild_is_server_specific()
    @commands.bot_has_permissions(send_messages=True)
    async def incest_disallow(self, ctx:voxelbotutils.Context):
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

    @voxelbotutils.command(aliases=['ssf', 'incest'])
    @commands.bot_has_permissions(send_messages=True)
    async def gold(self, ctx:voxelbotutils.Context):
        """
        Gives you the information about server specific families and MarriageBot Gold.
        """

        try:
            await ctx.author.send(MARRIAGEBOT_GOLD_INFORMATION.strip())
            await ctx.send("Sent you a DM!")
        except discord.Forbidden:
            await ctx.send("I couldn't send you a DM :c")


def setup(bot:voxelbotutils.Bot):
    x = ServerSpecific(bot)
    bot.add_cog(x)
