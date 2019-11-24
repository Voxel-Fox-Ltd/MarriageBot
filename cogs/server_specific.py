from asyncpg import UniqueViolationError
from discord.ext.commands import command, Context, check, CheckFailure, MissingPermissions, MissingRequiredArgument, BadArgument, CommandOnCooldown, MissingRole

from cogs.utils.checks.is_bot_moderator import is_server_specific_bot_moderator
from cogs.utils.custom_bot import CustomBot
from cogs.utils.custom_cog import Cog
from cogs.utils.checks.is_server_specific import is_server_specific, NotServerSpecific


class ServerSpecific(Cog):
    """A cog to group together all of the server specific commands"""

    def __init__(self, bot:CustomBot):
        super().__init__(self.__class__.__name__)
        self.bot = bot

    async def cog_command_error(self, ctx:Context, error):
        """Local error handler for the cog"""

        # Throw errors properly for me
        if ctx.original_author_id in self.bot.owners and not isinstance(error, (CommandOnCooldown, MissingPermissions)):
            text = f'```py\n{error}```'
            await ctx.send(text)
            raise error

        # Not server specific
        elif isinstance(error, NotServerSpecific):
            await ctx.send(f"You need to be running the server specific version of MarriageBot for this command to work (see `{ctx.clean_prefix}ssf` for more information).")
            return

        # Missing argument
        elif isinstance(error, MissingRequiredArgument):
            await ctx.send("You need to specify a person for this command to work properly.")
            return


        # Argument conversion error
        elif isinstance(error, BadArgument):
            try:
                argument_text = self.bot.bad_argument.search(str(error)).group(2)
                await ctx.send(f"User `{argument_text}` could not be found.")
            except Exception:
                await ctx.send(str(error))
            return

        # Missing permissions
        elif isinstance(error, MissingRole):
            if ctx.original_author_id in self.bot.owners:
                await ctx.reinvoke()
                return
            await ctx.send(f"You need the `{error.missing_role}` role to run this command.")
            return

    @Cog.listener()
    async def on_guild_join(self, guild):
        if self.bot.is_server_specific:
            async with self.bot.database() as db:
                data = await db('SELECT guild_id FROM guild_specific_families WHERE guild_id=$1', guild.id)
                if not data:
                    self.log_handler.warn(f"Automatically left guild {guild.name} ({guild.id}) for non-subscription")
                    await guild.leave()
                    return

    @command()
    @is_server_specific_bot_moderator()
    @is_server_specific()
    async def allowincest(self, ctx:Context):
        """Toggles allowing incest on your guild"""

        # Database it
        async with self.bot.database() as db:
            try:
                await db(
                    'INSERT INTO guild_settings (guild_id, prefix, allow_incest) VALUES ($1, $2, $3)',
                    ctx.guild.id, self.bot.config['prefix']['default_prefix'], True,
                )
            except UniqueViolationError:
                await db(
                    'UPDATE guild_settings SET allow_incest=$2 WHERE guild_id=$1',
                    ctx.guild.id, True,
                )

        # Cache it
        try:
            self.bot.guild_settings[ctx.guild.id]['allow_incest'] = True
        except KeyError:
            self.bot.guild_settings[ctx.guild.id] = {
                'allow_incest': True,
                'prefix': self.bot.config['prefix']['default_prefix'],
            }

        # Boop the user
        await ctx.send("Incest is now **ALLOWED** on your guild.")

    @command()
    @is_server_specific_bot_moderator()
    @is_server_specific()
    async def disallowincest(self, ctx:Context):
        """Toggles allowing incest on your guild"""

        # Database it
        async with self.bot.database() as db:
            try:
                await db(
                    'INSERT INTO guild_settings (guild_id, prefix, allow_incest) VALUES ($1, $2, $3)',
                    ctx.guild.id, self.bot.config['prefix']['default_prefix'], False,
                )
            except UniqueViolationError:
                await db(
                    'UPDATE guild_settings SET allow_incest=$2 WHERE guild_id=$1',
                    ctx.guild.id, False,
                )

        # Cache it
        try:
            self.bot.guild_settings[ctx.guild.id]['allow_incest'] = False
        except KeyError:
            self.bot.guild_settings[ctx.guild.id] = {
                'allow_incest': False,
                'prefix': self.bot.config['prefix']['default_prefix'],
            }

        # Boop the user
        await ctx.send("Incest is now **DISALLOWED** on your guild.")

    @command(aliases=['ssf'])
    async def serverspecificfamilies(self, ctx:Context):
        """Gives you the information about server specific families and MarriageBot gold"""

        await ctx.send(f"MarriageBot Gold (the server specific version of MarriageBot) is a one time payment of £20 GBP (~$25 USD, price may adjust over time). It's a new bot you add to your server (MarriageBot Gold) that has a non configurable prefix of `m.`. When you add the bot, any user on your server with a role named \"MarriageBot Moderator\" is able to run the force commands (ie `forceadopt`, `forceeman`, `forcedivorce`, `forcemarry`). The 500 person limit still applies. The children limits still apply (though this may change in future, and become configurable also). The tree command cooldown is reduced to 5 seconds for all users. You're also able to allow incestuous relationships on your server via the `allowincest` and `disallowincest` commands. Since it's a separate bot, you can have both bots on your server at once, if it's something you want to do.\n\nIf you'd like to know more, contact `Caleb` at `{ctx.clean_prefix}support`.")


def setup(bot:CustomBot):
    x = ServerSpecific(bot)
    bot.add_cog(x)
