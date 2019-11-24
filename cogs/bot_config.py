import asyncpg
from discord.ext import commands

from cogs import utils


class BotConfig(utils.Cog):

    async def cog_check(self, ctx:utils.Context):
        """Only users with the manage_guild permission can run these commands"""

        if ctx.author.permissions_in(ctx.channel).manage_guild:
            return True
        raise commands.MissingPermissions(["manage_guild"])

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def prefix(self, ctx:utils.Context, prefix:str=None):
        """Changes the prefix for your guild"""

        # Fix up prefix
        if not prefix:
            prefix = self.bot.config['prefix']['default_prefix']
        if len(prefix) > 30:
            await ctx.send("Your prefix can't be longer than 30 characters.")
            return

        # Update db
        async with self.bot.database() as db:
            try:
                await db('INSERT INTO guild_settings VALUES ($1, $2)', ctx.guild.id, prefix)
            except asyncpg.UniqueViolationError:
                await db('UPDATE guild_settings SET prefix=$1 WHERE guild_id=$2', prefix, ctx.guild.id)

        # Update cache
        self.bot.guild_settings[ctx.guild.id]['prefix'] = prefix
        await ctx.send(f"Your guild's prefix has been updated to `{prefix}`.")


def setup(bot:utils.CustomBot):
    x = BotConfig(bot)
    bot.add_cog(x)
