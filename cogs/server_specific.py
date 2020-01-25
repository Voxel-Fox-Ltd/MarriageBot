import discord
from discord.ext import commands

from cogs import utils


class ServerSpecific(utils.Cog):

    @utils.Cog.listener()
    async def on_guild_join(self, guild:discord.Guild):
        """Looks for when the bot is added to a guild, leaving if it's not whitelisted"""

        # Only work with Gold
        if not self.bot.is_server_specific:
            return

        # See if we should be here
        async with self.bot.database() as db:
            data = await db('SELECT guild_id FROM guild_specific_families WHERE guild_id=$1', guild.id)
        if data:
            return

        # Leave server
        self.logger.warn(f"Automatically left guild {guild.name} ({guild.id}) for non-subscription")
        await guild.leave()

    @commands.command(cls=utils.Command)
    @utils.checks.is_server_specific_bot_moderator()
    @utils.checks.guild_is_server_specific()
    async def allowincest(self, ctx:utils.Context):
        """Toggles allowing incest on your guild"""

        async with self.bot.database() as db:
            await db(
                'INSERT INTO guild_settings (guild_id, prefix, allow_incest) VALUES ($1, $2, $3) ON CONFLICT (guild_id) DO UPDATE SET allow_incest=$3',
                ctx.guild.id, self.bot.guild_settings[ctx.guild.id]['prefix'], False,
            )
        self.bot.guild_settings[ctx.guild.id]['allow_incest'] = True
        await ctx.send("Incest is now **ALLOWED** on your guild.")

    @commands.command(cls=utils.Command)
    @utils.checks.is_server_specific_bot_moderator()
    @utils.checks.guild_is_server_specific()
    async def disallowincest(self, ctx:utils.Context):
        """Toggles allowing incest on your guild"""

        async with self.bot.database() as db:
            await db(
                'INSERT INTO guild_settings (guild_id, prefix, allow_incest) VALUES ($1, $2, $3) ON CONFLICT (guild_id) DO UPDATE SET allow_incest=$3',
                ctx.guild.id, self.bot.guild_settings[ctx.guild.id]['prefix'], False,
            )
        self.bot.guild_settings[ctx.guild.id]['allow_incest'] = False
        await ctx.send("Incest is now **DISALLOWED** on your guild.")

    @commands.command(aliases=['ssf'], cls=utils.Command)
    async def serverspecificfamilies(self, ctx:utils.Context):
        """Gives you the information about server specific families and MarriageBot gold"""

        await ctx.send(f"[See here](https://marriagebot.xyz/blog/gold) for a rundown of everything, or `m!perks` for an overview. Ask any questions you have at `m!support`.")


def setup(bot:utils.Bot):
    x = ServerSpecific(bot)
    bot.add_cog(x)
