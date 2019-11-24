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
                self.log_handler.warn(f"Automatically left guild {guild.name} ({guild.id}) for non-subscription")
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

        await ctx.send(f"MarriageBot Gold (the server specific version of MarriageBot) is a one time payment of £20 GBP (~$25 USD, price may adjust over time). It's a new bot you add to your server (MarriageBot Gold) that has a non configurable prefix of `m.`. When you add the bot, any user on your server with a role named \"MarriageBot Moderator\" is able to run the force commands (ie `forceadopt`, `forceeman`, `forcedivorce`, `forcemarry`). The 500 person limit still applies. The children limits still apply (though this may change in future, and become configurable also). The tree command cooldown is reduced to 5 seconds for all users. You're also able to allow incestuous relationships on your server via the `allowincest` and `disallowincest` commands. Since it's a separate bot, you can have both bots on your server at once, if it's something you want to do.\n\nIf you'd like to know more, contact `Caleb` at `{ctx.clean_prefix}support`.")


def setup(bot:utils.CustomBot):
    x = ServerSpecific(bot)
    bot.add_cog(x)
