import asyncio
import typing

import discord
from discord.ext import commands

from cogs import utils


class SettingsMenuError(commands.CommandError):
    pass


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
            emoji:str=None, allow_nullable:bool=True,
            ):
        self.context = ctx
        self._display = display
        self.args = converter_args
        self.callback = callback
        self.emoji = emoji
        self.allow_nullable = allow_nullable

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
            try:
                data = await self.convert_prompted_information(*i)
            except SettingsMenuError as e:
                if not self.allow_nullable:
                    raise e
                data = None
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
        conversion_failed = False
        if hasattr(converter, 'convert'):
            try:
                converter = converter()
            except TypeError:
                pass
            try:
                value = await converter.convert(self.context, content)
            except commands.CommandError:
                value = None
                conversion_failed = True
        else:
            try:
                value = converter(content)
            except Exception:
                value = None
                conversion_failed = True

        # Delete prompt messages
        try:
            await bot_message.delete()
        except discord.NotFound:
            pass
        try:
            await user_message.delete()
        except (discord.Forbidden, discord.NotFound, AttributeError):
            pass

        # Check conversion didn't fail
        if conversion_failed:
            raise SettingsMenuError()

        # Return converted value
        return value

    @classmethod
    def get_guild_settings_mention(cls, ctx:commands.Context, attr:str, default:str='none'):
        """Get an item from the bot's guild settings"""

        settings = ctx.bot.guild_settings[ctx.guild.id]
        return cls.get_settings_mention(ctx, settings, attr, default)

    @classmethod
    def get_user_settings_mention(cls, ctx:commands.Context, attr:str, default:str='none'):
        """Get an item from the bot's user settings"""

        settings = ctx.bot.user_settings[ctx.author.id]
        return cls.get_settings_mention(ctx, settings, attr, default)

    @classmethod
    def get_settings_mention(cls, ctx:commands.Context, settings:dict, attr:str, default:str='none'):
        """Get an item from the bot's settings"""

        # Run converters
        if 'channel' in attr.lower().split('_'):
            data = ctx.bot.get_channel(settings[attr])
        elif 'role' in attr.lower().split('_'):
            data = ctx.guild.get_role(settings[attr])
        else:
            data = settings[attr]
            if isinstance(data, bool):
                return str(data).lower()
            return data

        # Get mention
        return cls.get_mention(data, default)

    @staticmethod
    def get_mention(data, default:str):
        """Get the mention of an object"""

        mention = data.mention if data else default
        return mention

    @staticmethod
    def get_set_guild_settings_callback(database_name:str, database_key:str, serialize_function:typing.Callable[[typing.Any], typing.Any]=lambda x: x):
        """Return an async method that takes the data retuend by convert_prompted_information and then
        saves it into the database - should be used for the add_option stuff in the SettingsMenu init

        Params:
            table_name : str
                The name of the table the data should be inserted into
                This is not used when caching information
                This should NOT be a user supplied value
            database_key : str
                The name of the column that the data should be inserted into
                This is the same name that's used for caching
                This should NOT be a user supplied value
            serialize_function : typing.Callable[[typing.Any], typing.Any]
                The function that is called to convert the input data in the callback into a database-friendly value
                This is _not_ called for caching the value, only for databasing
                The default serialize function doesn't do anything, but is provided so you don't have to provide one yourself
        """

        async def callback(self, data):
            """The function that actually sets the data in the specified table in the database
            Any input to this function should be a direct converted value from `convert_prompted_information`
            If the input is a discord.Role or discord.TextChannel, it is automatcally converted to that value's ID,
            which is then put into the datbase and cache
            """

            if isinstance(data, (discord.Role, discord.TextChannel)):
                data = data.id
            original_data, data = data, serialize_function(data)

            async with self.context.bot.database() as db:
                await db(
                    "INSERT INTO {0} (guild_id, {1}) VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET {1}=$2".format(database_name, database_key),
                    self.context.guild.id, data
                )
            self.context.bot.guild_settings[self.context.guild.id][database_key] = original_data
        return callback

    @staticmethod
    def get_set_user_settings_callback(table_name:str, database_key:str, serialize_function:typing.Callable[[typing.Any], typing.Any]=lambda x: x):
        """Return an async method that takes the data retuend by convert_prompted_information and then
        saves it into the database - should be used for the add_option stuff in the SettingsMenu init

        Params:
            table_name : str
                The name of the table the data should be inserted into
                This is not used when caching information
                This should NOT be a user supplied value
            database_key : str
                The name of the column that the data should be inserted into
                This is the same name that's used for caching the value
                This should NOT be a user supplied value
            serialize_function : typing.Callable[[typing.Any], typing.Any]
                The function that is called to convert the input data in the callback into a database-friendly value
                This is _not_ called for caching the value, only for databasing
                The default serialize function doesn't do anything, but is provided so you don't have to provide one yourself
        """

        async def callback(self, data):
            """The function that actually sets the data in the specified table in the database
            Any input to this function should be a direct converted value from `convert_prompted_information`
            If the input is a discord.Role or discord.TextChannel, it is automatcally converted to that value's ID,
            which is then put into the datbase and cache
            """

            if isinstance(data, (discord.Role, discord.TextChannel)):
                data = data.id
            original_data, data = data, serialize_function(data)

            async with self.context.bot.database() as db:
                await db(
                    "INSERT INTO {0} (user_id, {1}) VALUES ($1, $2) ON CONFLICT (user_id) DO UPDATE SET {1}=$2".format(table_name, database_key),
                    self.context.author.id, data
                )
            self.context.bot.user_settings[self.context.author.id][database_key] = original_data
        return callback

    @staticmethod
    def get_set_iterable_delete_callback(database_name:str, column_name:str, key_id:int, cache_key:str, database_key:str):
        """Return an async method that takes the data retuend by convert_prompted_information and then
        saves it into the database - should be used for the add_option stuff in the SettingsMenu init

        Params:
            database_name : str
                The name of the database that you want to remove data from
            column_name : str
                The column name that the key is inserted into in the table
            key_id : int
                The role that you want to remove from the `role_list` table
            guild_setting_key : str
                The key that's used to access the cached value for the iterable in `bot.guilds_settings`
            database_key : str
                The key that's used to refer to the role ID in the `role_list` table
        """

        async def callback(self, *data):
            """The function that actually deletes the role from the database
            Any input to this function will be silently discarded, since the actual input to this function is defined
            in the callback definition
            """

            # Database it
            async with self.context.bot.database() as db:
                await db(
                    "DELETE FROM {0} WHERE guild_id=$1 AND {1}=$2 AND key=$3".format(database_name, column_name),
                    self.context.guild.id, key_id, database_key
                )

            # Cache it
            try:
                self.context.bot.guild_settings[self.context.guild.id][cache_key].remove(key_id)
            except AttributeError:
                self.context.bot.guild_settings[self.context.guild.id][cache_key].pop(key_id)
        return callback

    @staticmethod
    def get_set_iterable_add_callback(database_name:str, column_name:str, cache_key:str, database_key:str, serialize_function:typing.Callable[[typing.Any], str]=lambda x: x):
        """Return an async method that takes the data retuend by convert_prompted_information and then
        saves it into the database - should be used for the add_option stuff in the SettingsMenu init

        Params:
            database_name : str
                The name of the database that you want to add data to
            column_name : str
                The column name that the key is inserted into in the table
            guild_setting_key : str
                This is the key that's used when caching the value in `bot.guild_settings`
            database_key : str
                This is the key that the value is added to the database table `role_list`
            serialize_function : typing.Callable[[typing.Any], str]
                The function run on the value to convert it into to make it database-safe
                Values are automatically cast to strings after being run through the serialize function
                The serialize_function is called when caching the value, but the cached value is not cast to a string
                The default serialize function doesn't do anything, but is provided so you don't have to provide one yourself
        """

        async def callback(self, *data):
            """The function that actually adds the role to the table in the database
            Any input to this function will be direct outputs from perform_action's convert_prompted_information
            This is a function that creates a callback, so the expectation of `data` in this instance is that data is either
            a list of one item for a listing, eg [role_id], or a list of two items for a mapping, eg [role_id, value]
            """

            # Unpack the data
            try:
                role, original_value = data
                value = str(serialize_function(original_value))
            except ValueError:
                role, value = data[0], None

            # Database it
            async with self.context.bot.database() as db:
                await db(
                    """INSERT INTO {0} (guild_id, {1}, key, value) VALUES ($1, $2, $3, $4)
                    ON CONFLICT (guild_id, {1}, key) DO UPDATE SET value=excluded.value""".format(database_name, column_name),
                    self.context.guild.id, role.id, database_key, value
                )

            # Cache it
            if value:
                self.context.bot.guild_settings[self.context.guild.id][cache_key][role.id] = serialize_function(original_value)
            else:
                if role.id not in self.context.bot.guild_settings[self.context.guild.id][cache_key]:
                    self.context.bot.guild_settings[self.context.guild.id][cache_key].append(role.id)
        return callback


class SettingsMenu(object):
    """A settings menu object for setting up sub-menus or bot settings
    Each menu object must be added as its own command, with sub-menus being
    referred to by string in the MenuItem's action
    """

    TICK_EMOJI = "\N{HEAVY CHECK MARK}"
    PLUS_EMOJI = "\N{HEAVY PLUS SIGN}"

    def __init__(self):
        self.items: typing.List[SettingsMenuOption] = list()
        self.emoji_options: typing.Dict[str, SettingsMenuOption] = {}

    def add_option(self, option:SettingsMenuOption):
        """Add an option to the settings list"""

        self.items.append(option)

    def bulk_add_options(self, ctx:commands.Context, *args):
        """Add MULTIPLE options to the settings list
        Each option is simply thrown into a SettingsMenuOption item and then added to the options list
        """

        for data in args:
            self.add_option(SettingsMenuOption(ctx, **data))

    async def start(self, ctx:commands.Context, *, timeout:float=120, clear_reactions_on_loop:bool=False):
        """Actually run the menu

        Params:
            ctx : commands.Context
                The context object for the called command
            timeout : float
                How long the bot should wait for a reaction
            clear_reactions_on_loop : bool
                Exactly as it says - when the menu loops, should reactions be cleared?
                You only need to set this to True if the items in a menu change on loop
        """

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
            try:
                await picked_option.perform_action()
            except SettingsMenuError:
                pass

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
        """Get a valid set of sendable data for the destination

        Returns:
            Two arguments - a dict that is passed directly into a `.send`, and a list of emoji that
            should be added to that message
        """

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
    """A version of the settings menu for dealing with things like lists and dictionaries
    that are just straight read/stored in the database

    Params:
        database_name : str
            The name of the table that the data should be inserted into
        column_name : str
            The column name for the table where teh key should be inserted to
        cache_key : str
            The key that goes into `bot.guild_settings` to get to the cached iterable
        database_key : str
            The key that would be inserted into the default `role_list` or `channel_list` tables
        key_converter : commands.Converter
            The converter that's used to take the user's input and convert it into a given object
            Usually this will be a commands.RoleConverter or commands.TextChannelConverter
        key_prompt : str
            The string send to the user when asking for the key
        key_display_function : typing.Callable
            A function used to take the raw data from the key and change it into a display value
        value_converter : commands.Converter
            The converter that's used to take the user's input and change it into something of value
        value_serialize_function : typing.Callable
            A function used to take the converted value and change it into something database-friendly
    """

    def __init__(
            self, database_name:str, column_name:str, cache_key:str, database_key:str,
            key_converter:commands.Converter, key_prompt:str, key_display_function:typing.Callable[[typing.Any], str],
            value_converter:commands.Converter=str, value_prompt:str=None, value_serialize_function:typing.Callable=None,
            *, iterable_add_callback:typing.Callable=None, iterable_delete_callback:typing.Callable=None,
            ):
        super().__init__()

        # Set up the storage data
        self.database_name = database_name
        self.column_name = column_name
        self.cache_key = cache_key
        self.database_key = database_key

        # Key conversion
        self.key_converter = key_converter
        self.key_prompt = key_prompt
        self.key_display_function = key_display_function

        # Value conversion
        self.value_converter = value_converter
        self.value_prompt = value_prompt
        self.value_serialize_function = value_serialize_function or (lambda x: x)

        # Callbacks
        self.iterable_add_callback = iterable_add_callback or SettingsMenuOption.get_set_iterable_add_callback
        self.iterable_delete_callback = iterable_delete_callback or SettingsMenuOption.get_set_iterable_delete_callback

    def get_sendable_data(self, ctx:commands.Context):
        """Create a list of mentions from the given guild settings key, creating all relevant callbacks"""

        # Get the current data
        data_points = ctx.bot.guild_settings[ctx.guild.id][self.cache_key]

        # Current data is a key-value pair
        if isinstance(data_points, dict):
            self.items = [
                SettingsMenuOption(
                    ctx, f"{self.key_display_function(i)} - {self.value_converter(o)!s}", (),
                    self.iterable_delete_callback(self.database_name, self.column_name, i, self.cache_key, self.database_key),
                    allow_nullable=False,
                )
                for i, o in data_points.items()
            ]
            if len(self.items) < 10:
                self.items.append(
                    SettingsMenuOption(
                        ctx, "", [
                            (self.key_prompt, "value", self.key_converter),
                            (self.value_prompt, "value", self.value_converter)
                        ], self.iterable_add_callback(self.database_name, self.column_name, self.cache_key, self.database_key, self.value_serialize_function),
                        emoji=self.PLUS_EMOJI,
                        allow_nullable=False,
                    )
                )

        # Current data is a key list
        elif isinstance(data_points, list):
            self.items = [
                SettingsMenuOption(
                    ctx, f"{self.key_display_function(i)}", (),
                    self.iterable_delete_callback(self.database_name, self.column_name, i, self.cache_key, self.database_key),
                    allow_nullable=False,
                )
                for i in data_points
            ]
            if len(self.items) < 10:
                self.items.append(
                    SettingsMenuOption(
                        ctx, "", [
                            (self.key_prompt, "value", self.key_converter),
                        ], self.iterable_add_callback(self.database_name, self.column_name, self.cache_key, self.database_key),
                        emoji=self.PLUS_EMOJI,
                        allow_nullable=False,
                    )
                )

        # Generate the data as normal
        return super().get_sendable_data(ctx)

    async def start(*args, clear_reactions_on_loop:bool=True, **kwargs):
        super().start(*args, clear_reactions_on_loop=clear_reactions_on_loop, **kwargs)
