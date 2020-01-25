import asyncpg
from discord.ext import commands

from cogs import utils


class BotSettings(utils.Cog):

    @commands.command(cls=utils.Command)
    @commands.guild_only()
    @commands.bot_has_permissions(send_messages=True)
    @commands.has_permissions(manage_guild=True)
    async def prefix(self, ctx:utils.Context, *, new_prefix:str=None):
        """Changes the prefix that the bot uses"""

        # Fix up prefix
        if not new_prefix:
            prefix = self.bot.config['prefix']['default_prefix']
        if len(prefix) > 30:
            await ctx.send("Your prefix can't be longer than 30 characters.")
            return

        # Update db
        prefix_key = 'gold_prefix' if self.bot.is_server_specific else 'prefix'
        async with self.bot.database() as db:
            try:
                await db(f'INSERT INTO guild_settings (guild_id, {prefix_key}) VALUES ($1, $2)', ctx.guild.id, prefix)
            except asyncpg.UniqueViolationError:
                await db(f'UPDATE guild_settings SET {prefix_key}=$1 WHERE guild_id=$2', prefix, ctx.guild.id)

        # Update cache
        self.bot.guild_settings[ctx.guild.id]['prefix'] = prefix
        await ctx.send(f"Your guild's prefix has been updated to `{prefix}`.")


def setup(bot:utils.Bot):
    x = BotSettings(bot)
    bot.add_cog(x)
