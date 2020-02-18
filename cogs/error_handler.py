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
            utils.errors.IsNotDonator, utils.errors.IsNotPatreon, utils.errors.IsNotPaypal,
            utils.errors.IsNotVoter, commands.MissingAnyRole, commands.MissingPermissions,
            commands.MissingRole, commands.CommandOnCooldown, commands.DisabledCommand,
            utils.errors.BlockedUserError, utils.errors.BotNotReady,
        )
        if ctx.original_author_id in self.bot.owner_ids and isinstance(error, owner_reinvoke_errors):
            return await ctx.reinvoke()

        # Can't send files
        if isinstance(error, utils.errors.CantSendFiles):
            return await self.send_to_ctx_or_author(ctx,
                "I'm not able to send files into this channel.",
                "I'm unable to send messages into that channel."
            )

        # Cooldown
        elif isinstance(error, commands.CommandOnCooldown):
            if ctx.command.name in ['familytree']:
                return await self.tree_timeout_handler(ctx, error)
            return await ctx.send(f"You can only use this command once every `{error.cooldown.per:.0f} seconds` per server. You may use this again in `{error.retry_after:.2f} seconds`.")

        # Voter
        elif isinstance(error, utils.errors.IsNotVoter):
            return await ctx.send(f"You need to vote on DBL (`m!vote`) to be able to run this command.")

        # Donator
        elif isinstance(error, utils.errors.IsNotDonator):
            return await ctx.send(f"You need to be a Patreon subscriber (`m!perks`) to be able to run this command.")

        # Not a server specific bot moderator
        elif isinstance(error, utils.errors.NotBotModerator):
            if self.bot.is_server_specific:
                return await ctx.send(f"You're missing the `MarriageBot Moderator` role required for this command.")
            return await ctx.send(f"This instance of the bot is not set to server specific.")

        # Not a bot administrator
        elif isinstance(error, utils.errors.NotBotAdministrator):
            return await ctx.send(f"You need to be registered as MarriageBot support to run this command.")

        # Not set to server specific
        elif isinstance(error, utils.errors.NotServerSpecific):
            return await ctx.send(f"You need to be using MarriageBot Gold to run this command - see (`m!perks`).")

        # User is blocked
        elif isinstance(error, utils.errors.BlockedUserError):
            return await ctx.send(str(error))

        # Bot ready
        elif isinstance(error, utils.errors.BotNotReady):
            return await ctx.send("The bot isn't ready to start processing that command yet - please wait.")

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

    async def tree_timeout_handler(self, ctx:utils.Context, error):
        """Handles errors for the tree commands"""

        # Get user perks
        if self.bot.is_server_specific:
            perk_index = -2
        else:
            perk_index = await utils.checks.get_patreon_tier(self.bot, ctx.author)
            if utils.checks.is_voter_predicate(ctx) and perk_index <= 0:
                perk_index = -1
        cooldown_time = {
            -2: 5,
            -1: 30,
            0: error.cooldown.per,
            1: 15,
            2: 15,
            3: 5,
        }.get(perk_index)  # perk_index = range(-2, 3) = server_specific, donator, none, patron...

        # See if they're able to call the command
        if (error.cooldown.per - cooldown_time) > error.retry_after:
            ctx.command.reset_cooldown(ctx)
            return await ctx.command.invoke(ctx)

        # Make the error message we want to display
        cooldown_display = f"{error.cooldown.per:.0f} seconds"
        time_remaining = error.retry_after
        if cooldown_time < error.cooldown.per:
            cooldown_display = f"~~{cooldown_display}~~ {cooldown_time:.0f} seconds"
            time_remaining = cooldown_time - (error.cooldown.per - error.retry_after)
        await ctx.send(f"You can only use this command once every {cooldown_display} (see `m!perks` for more information) per server. You may use this again in {time_remaining:.1f} seconds.")


def setup(bot:utils.Bot):
    x = ErrorHandler(bot)
    bot.add_cog(x)
