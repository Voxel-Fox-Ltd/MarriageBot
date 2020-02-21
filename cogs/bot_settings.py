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
            new_prefix = self.bot.config['prefix']['default_prefix']
        if len(new_prefix) > 30:
            return await ctx.send("Your prefix can't be longer than 30 characters.")

        # Update db
        prefix_key = 'gold_prefix' if self.bot.is_server_specific else 'prefix'
        async with self.bot.database() as db:
            await db(f'INSERT INTO guild_settings (guild_id, {prefix_key}) VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET {prefix_key}=$2', ctx.guild.id, new_prefix)

        # Update cache
        self.bot.guild_settings[ctx.guild.id]['prefix'] = new_prefix
        await ctx.send(f"Your guild's prefix has been updated to `{new_prefix}`.")


    @commands.command(cls=utils.Command)
    @commands.guild_only()
    @commands.bot_has_permissions(send_messages=True)
    @commands.has_permissions(manage_guild=True)
    async def togglegif(self, ctx:utils.Context, command:str=None, toggle:str=None):
        """Changes whether the bot shows gifs or not depending on command."""
        
        if not toggle:
            toggle = True

        # Update db
        async with self.bot.database() as db:
            await db(f'INSERT INTO guild_command_settings (guild_id, command_{command}, {toggle.upper()}) VALUES ($1, $2, $3) ON CONFLICT (command_{command}) DO UPDATE SET {toggle}=$3', ctx.guild.id, f"command_{command}", toggle.upper())

        # Update cache
        self.bot.guild_settings[ctx.guild.id][command] = toggle
        if toggle:
            await ctx.send(f"`{command}` will now show gifs.")
        else:
            await ctx.send(f"`{command}` will now not show gifs.")


def setup(bot:utils.Bot):
    x = BotSettings(bot)
    bot.add_cog(x)
