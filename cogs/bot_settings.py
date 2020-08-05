from discord.ext import commands

from cogs import utils


class BotSettings(utils.Cog):

    @commands.command(cls=utils.Command)
    @commands.has_permissions(manage_guild=True)
    @commands.bot_has_permissions(send_messages=True)
    @commands.guild_only()
    async def prefix(self, ctx:utils.Context, *, new_prefix:str):
        """Changes the prefix that the bot uses"""

        # Fix up prefix
        if not new_prefix:
            new_prefix = self.bot.config['prefix']['default_prefix']
        if len(new_prefix) > 30:
            return await ctx.send("The maximum length a prefix can be is 30 characters.")

        # Update db
        prefix_key = 'gold_prefix' if self.bot.is_server_specific else 'prefix'
        async with self.bot.database() as db:
            await db(f'INSERT INTO guild_settings (guild_id, {prefix_key}) VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET {prefix_key}=$2', ctx.guild.id, new_prefix)

        # Update cache
        self.bot.guild_settings[ctx.guild.id]['prefix'] = new_prefix
        await ctx.send(f"Your guild's prefix has been updated to `{new_prefix}`.")

    @commands.group(cls=utils.Group, enabled=False)
    @commands.has_permissions(manage_guild=True)
    @commands.bot_has_permissions(send_messages=True, embed_links=True, add_reactions=True)
    @commands.guild_only()
    async def setup(self, ctx:utils.Context):
        """Run the bot setup"""

        # Make sure it's only run as its own command, not a parent
        if ctx.invoked_subcommand is not None:
            return

        # Create settings menu
        menu = utils.SettingsMenu()
        settings_mention = utils.SettingsMenuOption.get_guild_settings_mention
        menu.bulk_add_options(
            ctx,
            {
                'display': lambda c: "Set setting (currently {0})".format(settings_mention(c, 'setting_id')),
                'converter_args': [("What do you want to set the setting to?", "setting channel", commands.TextChannelConverter)],
                'callback': utils.SettingsMenuOption.get_set_guild_settings_callback('guild_settings', 'setting_id'),
            },
        )
        try:
            await menu.start(ctx)
            await ctx.send("Done setting up!")
        except utils.errors.InvokedMetaCommand:
            pass

    @commands.group(cls=utils.Group, enabled=False)
    @commands.bot_has_permissions(send_messages=True, embed_links=True, add_reactions=True)
    @utils.cooldown.cooldown(1, 60, commands.BucketType.member)
    @commands.guild_only()
    async def usersettings(self, ctx:utils.Context):
        """Run the bot setup"""

        # Make sure it's only run as its own command, not a parent
        if ctx.invoked_subcommand is not None:
            return

        # Create settings menu
        menu = utils.SettingsMenu()
        settings_mention = utils.SettingsMenuOption.get_user_settings_mention
        menu.bulk_add_options(
            ctx,
            {
                'display': lambda c: "Set setting (currently {0})".format(settings_mention(c, 'setting_id')),
                'converter_args': [("What do you want to set the setting to?", "setting channel", commands.TextChannelConverter)],
                'callback': utils.SettingsMenuOption.get_set_user_settings_callback('user_settings', 'setting_id'),
            },
        )
        try:
            await menu.start(ctx)
            await ctx.send("Done setting up!")
        except utils.errors.InvokedMetaCommand:
            pass


def setup(bot:utils.Bot):
    x = BotSettings(bot)
    bot.add_cog(x)
