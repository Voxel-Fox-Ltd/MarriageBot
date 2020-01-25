import discord
from discord.ext import commands

from cogs import utils


class ErrorHandler(utils.Cog):

    async def send_to_ctx_or_author(self, ctx:utils.Context, text:str, author_text:str=None):
        """Tries to send the given text to ctx, but failing that, tries to send it to the author
        instead. If it fails that too, it just stays silent."""

        try:
            return await ctx.send(text)
        except discord.Forbidden:
            try:
                return await ctx.author.send(author_text or text)
            except discord.Forbidden:
                pass
        except discord.NotFound:
            pass
        return None

    @utils.Cog.listener()
    async def on_command_error(self, ctx:utils.Context, error:commands.CommandError):
        """Global error handler for all the commands around wew"""

        # Set up some errors that are just straight up ignored
        ignored_errors = (
            commands.CommandNotFound, utils.errors.InvokedMetaCommand,
        )
        if isinstance(error, ignored_errors):
            return

        # Set up some errors that the owners are able to bypass
        owner_reinvoke_errors = (
            commands.MissingAnyRole, commands.MissingPermissions,
            commands.MissingRole, commands.CommandOnCooldown, commands.DisabledCommand,
        )
        if ctx.original_author.id in self.bot.owner_ids and isinstance(error, owner_reinvoke_errors):
            return await ctx.reinvoke()

        # Missing argument (string)
        elif isinstance(error, utils.errors.MissingRequiredArgumentString):
            return await ctx.send(f"You're missing the `{error.param}` argument, which is required for this command to work properly.")

        # Missing argument
        elif isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send(f"You're missing the `{error.param.name}` argument, which is required for this command to work properly.")

        # Argument conversion error
        elif isinstance(error, commands.BadArgument):
            return await ctx.send(str(error))

        # NSFW channel
        elif isinstance(error, commands.NSFWChannelRequired):
            return await ctx.send("This command can't be run in a non-NSFW channel.")

        # Disabled command
        elif isinstance(error, commands.DisabledCommand):
            return await ctx.send("This command has been temporarily disabled. Apologies for any inconvenience.")

        # User is missing a role
        elif isinstance(error, commands.MissingAnyRole):
            return await ctx.send(f"You need to have one of the {', '.join(['`' + i + '`' for i in error.missing_roles])} roles to run this command.")

        # Bot is missing a given permission
        elif isinstance(error, commands.BotMissingPermissions):
            return await ctx.send(f"I'm missing the `{error.missing_perms[0]}` permission, which is needed for me to run this command.")

        # Missing permission
        elif isinstance(error, commands.MissingPermissions):
            return await ctx.send(f"You need the `{error.missing_perms[0]}` permission to run this command.")

        # Missing role
        elif isinstance(error, commands.MissingRole):
            return await ctx.send(f"You need to have the `{error.missing_role}` role to run this command.")

        # Guild only
        elif isinstance(error, commands.NoPrivateMessage):
            return await ctx.send(f"This command can't be run in DMs.")

        # DMs only
        elif isinstance(error, commands.PrivateMessageOnly):
            return await ctx.send(f"This command can only be run in DMs.")

        # Not owner
        elif isinstance(error, commands.NotOwner):
            return await ctx.send("You need to be registered as an owner to run this command.")

        # Can't tell what it is? Ah well.
        try:
            await ctx.send(f'```py\n{error}```')
        except (discord.Forbidden, discord.NotFound):
            pass
        raise error


def setup(bot:utils.Bot):
    x = ErrorHandler(bot)
    bot.add_cog(x)
