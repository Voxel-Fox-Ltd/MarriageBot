import random
import typing

import discord
from discord.ext import commands

from cogs import utils


class CustomHelpCommand(commands.MinimalHelpCommand):

    def __init__(self, **options):
        self.include_invite = options.pop("include_invite", True)
        super().__init__(**options)

    async def filter_commands(self, commands:typing.List[utils.Command]) -> typing.List[utils.Command]:
        """Filter the command list down into a list of _runnable_ commands"""

        if self.context.author.id in self.context.bot.owner_ids:
            return commands
        return [i for i in commands if i.hidden is False and i.enabled is True]

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
        data = {"embed": help_embed}
        if self.include_invite:
            data.update({"content": self.context.bot.config['command_data']['guild_invite']})
        await self.send_to_destination(**data)

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
            value = '\n'.join([self.get_help_line(command) for command in cog_commands])
            command_strings.append((getattr(cog, 'get_name', lambda: cog.name)(), value))

        # Order embed by length before embedding
        command_strings.sort(key=lambda x: len(x[1]), reverse=True)
        for name, value in command_strings:
            help_embed.add_field(
                name=name,
                value=value,
            )

        # Send it to the destination
        data = {"embed": help_embed}
        if self.include_invite:
            data.update({"content": self.context.bot.config['command_data']['guild_invite']})
        await self.send_to_destination(**data)

    async def send_to_destination(self, *args, **kwargs):
        """Sends content to the given destination"""

        dest = self.get_destination()

        # If the destination is a user
        if isinstance(dest, (discord.User, discord.Member, discord.DMChannel)):
            try:
                await dest.send(*args, **kwargs)
                if self.context.guild:
                    try:
                        await self.context.send("Sent you a DM!")
                    except discord.Forbidden:
                        pass  # Fail silently
            except discord.Forbidden:
                try:
                    await self.context.send("I couldn't send you a DM :c")
                except discord.Forbidden:
                    pass  # Oh no now they won't know anything
            return

        # If the destination is a channel
        try:
            await dest.send(*args, **kwargs)
        except discord.Forbidden:
            pass  # Can't talk in the channel? Shame

    def get_initial_embed(self) -> discord.Embed:
        """Get the initial embed for that gets sent"""

        embed = discord.Embed()
        embed.set_author(name=self.context.bot.user, icon_url=self.context.bot.user.avatar_url)
        embed.colour = random.randint(1, 0xffffff)
        return embed

    def get_help_line(self, command:utils.Command):
        """Gets a doc line of help for a given command"""

        if command.short_doc:
            return f"{self.clean_prefix}{command.qualified_name} - *{command.short_doc}*"
        return f"{self.clean_prefix}{command.qualified_name}"


class Help(utils.Cog):

    def __init__(self, bot:utils.Bot):
        super().__init__(bot)
        self._original_help_command = bot.help_command
        bot.help_command = CustomHelpCommand(dm_help=True)
        bot.help_command.cog = self

    def cog_unload(self):
        self.bot.help_command = self._original_help_command


def setup(bot:utils.Bot):
    x = Help(bot)
    bot.add_cog(x)
