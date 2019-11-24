import random

import discord
from discord.ext import commands

from cogs import utils


class HelpCommand(utils.Cog):
    """A cog exclusively made to hold the help command"""

    VISIBLE_ERRORS = (
        commands.BotMissingAnyRole, commands.BotMissingPermissions, commands.BotMissingRole,
        commands.MissingAnyRole, commands.MissingPermissions, commands.MissingRole,
        utils.errors.BotNotReady, utils.errors.CantSendFiles, utils.errors.IsNotDonator,
        utils.errors.NotServerSpecific, utils.errors.IsNotVoter,
    )  # A list of errors that, even if thrown, will still allow a command to be shown

    @commands.command(name='help', aliases=['commands'], hidden=True)
    async def newhelp(self, ctx:utils.Context, *, command_name:str=None):
        """The All New(tm) help command"""

        # Get all the cogs
        if not command_name:
            cogs = self.bot.cogs.values()
            cog_commands = [cog.get_commands() for cog in cogs]

        # Get the commands under a specific parent
        else:
            command = self.bot
            for i in command_name.split():
                command = command.get_command(i)
                if not command:
                    return await ctx.send(f"The command `{command_name}` could not be found.")
            if isinstance(command, commands.Group):
                cog_commands = [list(set(command.walk_commands()))]
            else:
                cog_commands = []

        # Check which commands are runnable
        runnable_commands = []
        for cog in cog_commands:
            visible_cog_commands = []
            for command in cog:
                visibility_checks = [
                    command.hidden is False or ctx.author.id in self.bot.owners,
                    command.enabled is True or ctx.author.id in self.bot.owners,
                ]
                try:
                    visibility_checks.append(await command.can_run(ctx))
                except Exception as e:
                    if not isinstance(e, self.VISIBLE_ERRORS):
                        visibility_checks.append(False)
                if all(visibility_checks):
                    visible_cog_commands.append(command)
            visible_cog_commands.sort(key=lambda x: x.name.lower())  # Sort alphabetically
            if len(visible_cog_commands) > 0:
                runnable_commands.append(visible_cog_commands)

        # Sort cogs list based on name
        runnable_commands.sort(key=lambda x: x[0].cog_name.lower())

        # Make an embed
        help_embed = discord.Embed()
        help_embed.set_author(name=self.bot.user, icon_url=self.bot.user.avatar_url)
        help_embed.colour = random.randint(1, 0xffffff)
        help_embed = ctx._set_footer(help_embed)

        # Add commands to it
        if command_name:
            help_embed.add_field(name=f"{ctx.prefix}{base_command.qualified_name}", value=f"{base_command.help}")
        for cog_commands in runnable_commands:
            value = '\n'.join([f"{ctx.prefix}{command.qualified_name} - *{command.short_doc}*" for command in cog_commands])
            value = value.replace(" - **", "")
            help_embed.add_field(
                name=cog_commands[0].cog_name,
                value=value
            )

        # Send it to the user
        try:
            await ctx.author.send(embed=help_embed)
            if ctx.guild:
                await ctx.send('Sent you a DM!')
        except Exception:
            await ctx.send("I couldn't send you a DM :c")


def setup(bot:utils.CustomBot):
    bot.remove_command('help')
    x = HelpCommand(bot)
    bot.add_cog(x)

