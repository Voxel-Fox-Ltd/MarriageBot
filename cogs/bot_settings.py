from discord.ext import commands
import asyncpg

from cogs import utils


class BotSettings(utils.Cog):

    @commands.command(cls=utils.Command)
    @commands.guild_only()
    @commands.bot_has_permissions(send_messages=True)
    async def prefix(self, ctx:utils.Context, *, new_prefix:str):
        """Changes the prefix that the bot uses"""

        if len(new_prefix) > 30:
            return await ctx.send(f"The maximum length a prefix can be is 30 characters.")
        self.bot.guild_settings[ctx.guild.id]['prefix'] = new_prefix
        async with self.bot.database() as db:
            try:
                await db("INSERT INTO guild_settings (guild_id, prefix) VALUES ($1, $2)", ctx.guild.id, new_prefix)
            except asyncpg.UniqueViolationError:
                await db("UPDATE guild_settings SET prefix=$2 WHERE guild_id=$1", ctx.guild.id, new_prefix)
        await ctx.send(f"My prefix has been updated to `{new_prefix}`.")


def setup(bot:utils.CustomBot):
    x = BotSettings(bot)
    bot.add_cog(x)

