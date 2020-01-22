import random
import typing

import discord
from discord.ext import commands

from cogs import utils


class CustomHelpCommand(commands.MinimalHelpCommand):

    def get_command_signature(self, command:commands.Command):
        return '{0.clean_prefix}{1.qualified_name} {1.signature}'.format(self, command)

    async def send_cog_help(self, cog:utils.Cog):
        """Sends help command for a cog"""

        return await self.send_bot_help({
            cog: cog.get_commands()
        })

    async def send_group_help(self, group:commands.Group):
        """Sends the help command for a given group"""

        return await self.send_bot_help({
            group: group.commands
        })

    async def send_command_help(self, command:utils.Command):
        """Sends the help command for a given command"""

        # Make an embed
        help_embed = self.get_initial_embed()

        # Add each command to the embed
        help_embed.add_field(
            name=f"{self.clean_prefix}{command.qualified_name} {command.signature}",
            value=f"{command.help}"
        )

        # Send it to the destination
        await self.send_to_destination(embed=help_embed)

    async def send_bot_help(self, mapping:typing.Dict[typing.Optional[utils.Cog], typing.List[commands.Command]]):
        """Sends all help to the given channel"""

        # Get the visible commands for each of the cogs
        runnable_commands = {}
        for cog, cog_commands in mapping.items():
            available_commands = await self.filter_commands(cog_commands)
            if len(available_commands) > 0:
                runnable_commands[cog] = available_commands

        # Make an embed
        help_embed = self.get_initial_embed()

        # Add each command to the embed
        command_strings = []
        for cog, cog_commands in runnable_commands.items():
            get_string = lambda c: f"{self.clean_prefix}{c.qualified_name} - *{c.short_doc}*" if c.short_doc else f"{self.clean_prefix}{c.qualified_name}"
            value = '\n'.join([get_string(command) for command in cog_commands])
            command_strings.append((getattr(cog, 'get_name', lambda: cog.name)(), value))

        # Order embed by length before embedding
        command_strings.sort(key=lambda x: len(x[1]), reverse=True)
        for name, value in command_strings:
            help_embed.add_field(
                name=name,
                value=value,
            )

        # Send it to the destination
        await self.send_to_destination(embed=help_embed)

    async def send_to_destination(self, *args, **kwargs):
        """Sends content to the given destination"""

        dest = self.get_destination()
        if isinstance(dest, (discord.User, discord.Member)):
            try:
                await dest.send(*args, **kwargs)
                if self.context.guild:
                    await self.context.send("Sent you a DM!")
            except Exception:
                await self.context.send("I couldn't send you a DM :c")
            return
        await dest.send(*args, **kwargs)

    def get_initial_embed(self) -> discord.Embed:
        """Get the initial embed for that gets sent"""

        embed = discord.Embed()
        embed.set_author(name=self.context.bot.user, icon_url=self.context.bot.user.avatar_url)
        embed.colour = random.randint(1, 0xffffff)
        return embed


class Help(utils.Cog):

    def __init__(self, bot:utils.Bot):
        super().__init__(bot)
        self._original_help_command = bot.help_command
        bot.help_command = CustomHelpCommand()
        bot.help_command.cog = self

    def cog_unload(self):
        self.bot.help_command = self._original_help_command


def setup(bot:utils.Bot):
    x = Help(bot)
    bot.add_cog(x)
