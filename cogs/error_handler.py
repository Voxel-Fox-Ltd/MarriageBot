import discord
from discord.ext import commands

from cogs import utils


class ErrorHandler(utils.Cog):

    async def send_to_ctx_or_author(self, ctx:utils.Context, text:str, author_text:str=None):
        """Tries to send the given text to ctx, but failing that, tries to send it to the author
        instead. If it fails that too, it just stays silent."""

        try:
            await ctx.send(text)
        except discord.Forbidden:
            try:
                await ctx.author.send(author_text or text)
            except discord.Forbidden:
                pass
        return

    @utils.Cog.listener()
    async def on_command_error(self, ctx:utils.Context, error:commands.CommandError):
        """Global error handler for all the commands around wew"""

        # Set up some errors that are just straight up ignored
        ignored_errors = (
            commands.CommandNotFound,
        )
        if isinstance(error, ignored_errors):
            return

        # Set up some errors that the owners are able to bypass
        owner_ignored_errors = (
            utils.errors.IsNotDonator, utils.errors.IsNotPatreon, utils.errors.IsNotPaypal,
            utils.errors.IsNotVoter, commands.MissingAnyRole, commands.MissingPermissions,
            commands.MissingRole, commands.CommandOnCooldown, commands.DisabledCommand,
        )
        if ctx.original_author_id in self.bot.owners and isinstance(error, owner_ignored_errors):
            return await ctx.reinvoke()
        elif ctx.original_author_id in self.bot.owners:
            await ctx.send(f'```py\n{error}```')
            raise error

        # Can't send files
        if isinstance(error, utils.errors.CantSendFiles):
            await self.send_to_ctx_or_author(ctx,
                "I'm not able to send files into this channel.",
                "I'm unable to send messages into that channel."
            )
            return

        # Missing argument
        elif isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send("You need to specify a person for this command to work properly.")

        # Cooldown
        elif isinstance(error, commands.CommandOnCooldown):
            if ctx.command.name in ['tree', 'globaltree']:
                cog = self.bot.get_cog("information")
                await cog.tree_timeout_handler(ctx, error)
            else:
                await ctx.send(f"You can only use this command once every `{error.cooldown.per:.0f} seconds` per server. You may use this again in `{error.retry_after:.2f} seconds`.")
            return

        # Voter
        elif isinstance(error, utils.errors.IsNotVoter):
            return await ctx.send(f"You need to vote on DBL (`{ctx.clean_prefix}vote`) to be able to run this command.")

        # Donator
        elif isinstance(error, utils.errors.IsNotDonator):
            return await ctx.send(f"You need to be a Patreon subscriber (`{ctx.clean_prefix}perks`) to be able to run this command.")

        # No item in config set
        elif isinstance(error, utils.errors.NoSetConfig):
            return await ctx.send(f"The bot owner has not set up their config properly for this command to work.")

        # Argument conversion error
        elif isinstance(error, commands.BadArgument):
            return await ctx.send(error)

        # Disabled command
        elif isinstance(error, commands.DisabledCommand):
            return await ctx.send("This command has been temporarily disabled. Apologies for any inconvenience.")

        # Bot ready
        elif isinstance(error, utils.errors.BotNotReady):
            return await ctx.send("The bot isn't ready to start processing that command yet - please wait.")

        # User is missing a role
        elif isinstance(error, commands.MissingAnyRole):
            return await ctx.send(f"You need to have the `{error.missing_roles[0]}` role to run this command.")

        # Bot is missing a given permission
        elif isinstance(error, commands.BotMissingPermissions):
            return await ctx.send(f"I'm missing the `{error.missing_perms[0]}` permission, which is needed for me to run this command.")

        # Missing permission
        elif isinstance(error, commands.MissingPermissions):
            return await ctx.send(f"You need the `{error.missing_perms[0]}` permission to run this command.")

        # Missing role
        elif isinstance(error, commands.MissingRole):
            return await ctx.send(f"You need to have the `{error.missing_role}` role to run this command.")


def setup(bot:utils.CustomBot):
    x = ErrorHandler(bot)
    bot.add_cog(x)
