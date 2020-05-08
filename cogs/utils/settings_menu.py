import asyncio
import typing

import discord
from discord.ext import commands

from cogs import utils


class SettingsMenuOption(object):
    """An option that can be chosen for a settings menu's selectable item,
    eg an option that refers to a sub-menu, or a setting that refers to grabbing
    a role list, etc

    Params:
        ctx
            The context for which the menu is being invoked
        display
            A string (or callable that returns string) that gives the display prompt for the option
        action
            A method (optionally coro) that is run when this option is chosen
            The first argument will be the option instance
        *args
            Tuples of (prompt, name, converter) that are thrown to convert_prompted_information
        callback
            A callable that's passed the information from the converter for you do to whatever with
    """

    def __init__(
            self, ctx:commands.Context, display:typing.Union[str, typing.Callable[[commands.Context], str]],
            converter_args:typing.List[typing.Tuple]=list(),
            callback:typing.Callable[['SettingsMenuOption', typing.List[typing.Any]], None]=lambda x: None,
            emoji:str=None
            ):
        self.context = ctx
        self._display = display
        self.args = converter_args
        self.callback = callback
        self.emoji = emoji

    def get_display(self) -> str:
        """Get the display prompt for this option"""

        if isinstance(self._display, str):
            return self._display
        return self._display(self.context)

    async def perform_action(self) -> None:
        """Performs the stored action using the given args and kwargs"""

        # Get data
        returned_data = []
        for i in self.args:
            data = await self.convert_prompted_information(*i)
            returned_data.append(data)
            if data is None:
                break

        # Do callback
        if isinstance(self.callback, commands.Command):
            await self.callback.invoke(self.context)
        else:
            called_data = self.callback(self, *returned_data)
            if asyncio.iscoroutine(called_data):
                await called_data

    async def convert_prompted_information(self, prompt:str, asking_for:str, converter:commands.Converter, reactions:typing.List[discord.Emoji]=list()) -> typing.Any:
        """Ask the user for some information, convert it, and return that converted value to the user

        Params:
            prompt
                The text that we sent to the user -- something along the lines of "what channel do you want to use" etc
            asking_for
                Say what we're looking for them to send - doesn't need to be anything important, it just goes to the timeout message
            converter
                The converter used to work out what to change the given user value to
        """

        # Send prompt
        bot_message = await self.context.send(prompt)
        if reactions:
            for r in reactions:
                await bot_message.add_reaction(r)
        try:
            if reactions:
                user_message = None
                check = lambda r, u: r.message.id == bot_message.id and u.id == self.context.author.id and str(r.emoji) in reactions
                reaction, _ = await self.context.bot.wait_for("reaction_add", timeout=120, check=check)
                content = str(reaction.emoji)
            else:
                check = lambda m: m.channel.id == self.context.channel.id and m.author.id == self.context.author.id
                user_message = await self.context.bot.wait_for("message", timeout=120, check=check)
                content = user_message.content
        except asyncio.TimeoutError:
            await self.context.send(f"Timed out asking for {asking_for}.")
            raise utils.errors.InvokedMetaCommand()

        # Run converter
        if hasattr(converter, 'convert'):
            try:
                converter = converter()
            except TypeError:
                pass
            try:
                value = await converter.convert(self.context, content)
            except commands.CommandError:
                value = None
        else:
            try:
                value = converter(content)
            except Exception:
                value = None

        # Delete prompt messages
        try:
            await bot_message.delete()
        except discord.NotFound:
            pass
        try:
            await user_message.delete()
        except (discord.Forbidden, discord.NotFound, AttributeError):
            pass

        # Return converted value
        return value

    @classmethod
    def get_guild_settings_mention(cls, ctx:commands.Context, attr:str, default:str='none'):
        """Get an item from the bot's guild settings"""

        # Set variables
        data = None
        settings = ctx.bot.guild_settings[ctx.guild.id]

        # Run converters
        if '_channel' in attr.lower():
            data = ctx.bot.get_channel(settings[attr])
        elif '_role' in attr.lower():
            data = ctx.guild.get_role(settings[attr])
        else:
            raise RuntimeError("Can't work out what you want to mention")

        # Get mention
        return cls.get_mention(data, default)

    @classmethod
    def get_user_settings_mention(cls, ctx:commands.Context, attr:str, default:str='none'):
        """Get an item from the bot's user settings"""

        # Set variables
        data = None
        settings = ctx.bot.user_settings[ctx.author.id]

        # Run converters
        if '_channel' in attr.lower():
            data = ctx.bot.get_channel(settings[attr])
        elif '_role' in attr.lower():
            data = ctx.guild.get_role(settings[attr])
        else:
            raise RuntimeError("Can't work out what you want to mention")

        # Get mention
        return cls.get_mention(data, default)

    @staticmethod
    def get_mention(data, default:str):
        """Get the mention of an object"""

        mention = data.mention if data else default
        return mention

    @staticmethod
    def get_set_guild_settings_callback(database_name:str, database_key:str):
        """Return an async method that takes the data retuend by convert_prompted_information and then
        saves it into the database - should be used for the add_option stuff in the SettingsMenu init"""

        async def callback(self, *data):
            data = data[0]  # Since data is returned as a tuple, we just want the first item from it
            if isinstance(data, (discord.Role, discord.TextChannel)):
                data = data.id

            async with self.context.bot.database() as db:
                await db(
                    "INSERT INTO {0} (guild_id, {1}) VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET {1}=$2".format(database_name, database_key),
                    self.context.guild.id, data
                )
            self.context.bot.guild_settings[self.context.guild.id][database_key] = data
        return callback

    @staticmethod
    def get_set_user_settings_callback(database_name:str, database_key:str):
        """Return an async method that takes the data retuend by convert_prompted_information and then
        saves it into the database - should be used for the add_option stuff in the SettingsMenu init"""

        async def callback(self, *data):
            data = data[0]  # Since data is returned as a tuple, we just want the first item from it
            if isinstance(data, (discord.Role, discord.TextChannel)):
                data = data.id

            async with self.context.bot.database() as db:
                await db(
                    "INSERT INTO {0} (user_id, {1}) VALUES ($1, $2) ON CONFLICT (user_id) DO UPDATE SET {1}=$2".format(database_name, database_key),
                    self.context.author.id, data
                )
            self.context.bot.user_settings[self.context.author.id][database_key] = data
        return callback

    @staticmethod
    def get_set_role_list_delete_callback(role_id:int, guild_settings_key:str, database_key:str):
        """Return an async method that takes the data retuend by convert_prompted_information and then
        saves it into the database - should be used for the add_option stuff in the SettingsMenu init"""

        async def callback(self, *data):
            # data should be an empty list if this is the callback
            async with self.context.bot.database() as db:
                await db(
                    "DELETE FROM role_list WHERE guild_id=$1 AND role_id=$2 AND key=$3",
                    self.context.guild.id, role_id, database_key
                )
            try:
                self.context.bot.guild_settings[self.context.guild.id][guild_settings_key].remove(role_id)
            except AttributeError:
                self.context.bot.guild_settings[self.context.guild.id][guild_settings_key].pop(role_id)
        return callback

    @staticmethod
    def get_set_role_list_add_callback(guild_settings_key:str, database_key:str, serialize_function:typing.Callable[[typing.Any], str]=lambda x: x):
        """Return an async method that takes the data retuend by convert_prompted_information and then
        saves it into the database - should be used for the add_option stuff in the SettingsMenu init"""

        async def callback(self, *data):
            # data will either be [role_id], or [role_id, value]
            try:
                role, value = data
                value = str(serialize_function(value))
            except ValueError:
                role, value = data[0], None
            async with self.context.bot.database() as db:
                await db(
                    """INSERT INTO role_list (guild_id, role_id, key, value) VALUES ($1, $2, $3, $4)
                    ON CONFLICT (guild_id, role_id, key) DO UPDATE SET value=excluded.value""",
                    self.context.guild.id, role.id, database_key, value
                )
            if value:
                self.context.bot.guild_settings[self.context.guild.id][guild_settings_key][role.id] = value
            else:
                if role.id not in self.context.bot.guild_settings[self.context.guild.id][guild_settings_key]:
                    self.context.bot.guild_settings[self.context.guild.id][guild_settings_key].append(role.id)
        return callback


class SettingsMenu(object):
    """A settings menu object for setting up sub-menus or bot settings
    Each menu object must be added as its own command, with sub-menus being
    referred to by string in the MenuItem's action
    """

    # TICK_EMOJI = "<:tickYes:596096897995899097>"
    TICK_EMOJI = "\N{HEAVY CHECK MARK}"
    PLUS_EMOJI = "\N{HEAVY PLUS SIGN}"

    def __init__(self):
        self.items: typing.List[SettingsMenuOption] = list()
        self.emoji_options: typing.Dict[str, SettingsMenuOption] = {}

    def add_option(self, option:SettingsMenuOption):
        """Add a pickable option to the settings menu"""

        self.items.append(option)

    def bulk_add_options(self, ctx:commands.Context, *args):
        """Add multiple options wew lad let's go"""

        for data in args:
            self.add_option(SettingsMenuOption(ctx, **data))

    async def start(self, ctx:commands.Context, *, timeout:float=120, clear_reactions_on_loop:bool=False):
        """Start up the menu, let's get this train rollin"""

        message = None
        while True:

            # Send message
            self.emoji_options.clear()
            data, emoji_list = self.get_sendable_data(ctx)
            sent_new_message = False
            if message is None:
                message = await ctx.send(**data)
                sent_new_message = True
            else:
                await message.edit(**data)
            if sent_new_message or clear_reactions_on_loop:
                for e in emoji_list:
                    await message.add_reaction(e)

            # Get the reaction
            try:
                check = lambda r, u: u.id == ctx.author.id and r.message.id == message.id
                reaction, _ = await ctx.bot.wait_for("reaction_add", check=check, timeout=timeout)
            except asyncio.TimeoutError:
                break
            picked_emoji = str(reaction.emoji)

            # Get the picked option
            try:
                picked_option = self.emoji_options[picked_emoji]
            except KeyError:
                continue

            # Process the picked option
            if picked_option is None:
                break
            await picked_option.perform_action()

            # Remove the emoji
            try:
                if clear_reactions_on_loop:
                    await reaction.message.clear_reactions()
                else:
                    await reaction.message.remove_reaction(picked_emoji, ctx.author)
            except discord.Forbidden:
                pass

        # Delete all the processing stuff
        try:
            await message.delete()
        except discord.NotFound:
            pass

    def get_sendable_data(self, ctx:commands.Context):
        """Send a valid embed to the destination"""

        ctx.invoke_meta = True

        # Create embed
        embed = discord.Embed()
        lines = []
        emoji_list = []
        index = 0
        for index, i in enumerate(self.items):
            emoji = i.emoji
            if emoji is None:
                emoji = f"{index}\N{COMBINING ENCLOSING KEYCAP}"
                index += 1
            display = i.get_display()
            if display:
                lines.append(f"{emoji} {i.get_display()}")
            self.emoji_options[emoji] = i
            emoji_list.append(emoji)

        # Finish embed
        text_lines = '\n'.join(lines)
        embed.description = text_lines or "No set data"

        # Add tick
        self.emoji_options[self.TICK_EMOJI] = None
        emoji_list.append(self.TICK_EMOJI)

        # Return data
        return {'embed': embed}, emoji_list


class SettingsMenuIterable(SettingsMenu):

    def __init__(
            self, guild_settings_key:str, guild_settings_database_key:str,
            key_converter:commands.Converter, key_prompt:str,
            value_converter:commands.Converter=str, value_prompt:str=None, value_serialize_function:typing.Callable=None
            ):
        super().__init__()
        self.guild_settings_key = guild_settings_key
        self.guild_settings_database_key = guild_settings_database_key
        self.key_converter = key_converter
        self.value_converter = value_converter
        self.key_prompt = key_prompt
        self.value_prompt = value_prompt
        self.value_serialize_function = value_serialize_function

    def get_sendable_data(self, ctx:commands.Context):
        """Create a list of mentions from the given guild settings key, creating all relevant callbacks"""

        # Get the current data
        data_points = ctx.bot.guild_settings[ctx.guild.id][self.guild_settings_key]

        # Current data is a key-value pair
        if isinstance(data_points, dict):
            self.items = [
                SettingsMenuOption(
                    ctx,
                    f"{SettingsMenuOption.get_mention(ctx.guild.get_role(i), 'none')} - {self.value_converter(o)!s}",
                    (),
                    SettingsMenuOption.get_set_role_list_delete_callback(i, self.guild_settings_key, self.guild_settings_database_key)
                )
                for i, o in data_points.items()
            ]
            self.items.append(
                SettingsMenuOption(
                    ctx, "", [
                        (self.key_prompt, "value", self.key_converter),
                        (self.value_prompt, "value", self.value_converter)
                    ], SettingsMenuOption.get_set_role_list_add_callback(self.guild_settings_key, self.guild_settings_database_key, self.value_serialize_function),
                    emoji=self.PLUS_EMOJI
                )
            )

        # Current data is a key list
        elif isinstance(data_points, list):
            self.items = [
                SettingsMenuOption(
                    ctx,
                    f"{SettingsMenuOption.get_mention(ctx.guild.get_role(i), 'none')}",
                    (),
                    SettingsMenuOption.get_set_role_list_delete_callback(i, self.guild_settings_key, self.guild_settings_database_key)
                )
                for i in data_points
            ]
            self.items.append(
                SettingsMenuOption(
                    ctx, "", [
                        (self.key_prompt, "value", self.key_converter),
                    ], SettingsMenuOption.get_set_role_list_add_callback(self.guild_settings_key, self.guild_settings_database_key),
                    emoji=self.PLUS_EMOJI
                )
            )

        # Generate the data as normal
        return super().get_sendable_data(ctx)
