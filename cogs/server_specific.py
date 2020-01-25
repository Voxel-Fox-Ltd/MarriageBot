import asyncpg
import discord
from discord.ext import commands

from cogs import utils


class ServerSpecific(utils.Cog):
    """A cog to group together all of the server specific commands"""

    @utils.Cog.listener()
    async def on_guild_join(self, guild:discord.Guild):
        """Looks for when the bot is added to a guild, leaving if it's not whitelisted"""

        if not self.bot.is_server_specific:
            return
        async with self.bot.database() as db:
            data = await db('SELECT guild_id FROM guild_specific_families WHERE guild_id=$1', guild.id)
            if not data:
                self.logger.warn(f"Automatically left guild {guild.name} ({guild.id}) for non-subscription")
                await guild.leave()

    @commands.command()
    @utils.checks.is_server_specific_bot_moderator()
    @utils.checks.guild_is_server_specific()
    async def allowincest(self, ctx:utils.Context):
        """Toggles allowing incest on your guild"""

        async with self.bot.database() as db:
            try:
                await db(
                    'INSERT INTO guild_settings (guild_id, prefix, allow_incest) VALUES ($1, $2, $3)',
                    ctx.guild.id, self.bot.guild_settings[ctx.guild.id]['prefix'], True,
                )
            except asyncpg.UniqueViolationError:
                await db(
                    'UPDATE guild_settings SET allow_incest=$2 WHERE guild_id=$1',
                    ctx.guild.id, True,
                )
        self.bot.guild_settings[ctx.guild.id]['allow_incest'] = True
        await ctx.send("Incest is now **ALLOWED** on your guild.")

    @commands.command()
    @utils.checks.is_server_specific_bot_moderator()
    @utils.checks.guild_is_server_specific()
    async def disallowincest(self, ctx:utils.Context):
        """Toggles allowing incest on your guild"""

        async with self.bot.database() as db:
            try:
                await db(
                    'INSERT INTO guild_settings (guild_id, prefix, allow_incest) VALUES ($1, $2, $3)',
                    ctx.guild.id, self.bot.guild_settings[ctx.guild.id]['prefix'], False,
                )
            except asyncpg.UniqueViolationError:
                await db(
                    'UPDATE guild_settings SET allow_incest=$2 WHERE guild_id=$1',
                    ctx.guild.id, False,
                )
        self.bot.guild_settings[ctx.guild.id]['allow_incest'] = False
        await ctx.send("Incest is now **DISALLOWED** on your guild.")

    @commands.command(aliases=['ssf'])
    async def serverspecificfamilies(self, ctx:utils.Context):
        """Gives you the information about server specific families and MarriageBot gold"""

        await ctx.send(f"[See here](https://marriagebot.xyz/blog/gold) for a rundown of everything, or `m!perks` for an overview. Ask any questions you have at `m!support`.")


def setup(bot:utils.Bot):
    x = ServerSpecific(bot)
    bot.add_cog(x)
