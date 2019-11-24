import traceback
import io
import textwrap
import contextlib
import copy

import discord
from discord.ext import commands

from cogs import utils


class OwnerOnly(utils.Cog):
    """Handles commands that only people registered as owners are able to run"""

    async def cog_check(self, ctx:utils.Context):
        """Checks that the ORIGINAL author (not counting sudo) is in the owners list"""

        if ctx.original_author_id in self.bot.owners:
            return True
        raise commands.NotOwner()

    @commands.command(aliases=['pm', 'dm'])
    async def message(self, ctx:utils.Context, user:utils.converters.UserID, *, content:str):
        """Messages a user the given content"""

        user_object = self.bot.get_user(user) or await self.bot.fetch_user(user)
        await user_object.send(content)
        await ctx.okay()

    def _cleanup_code(self, content):
        """Automatically removes code blocks from the code."""

        # Remove multiline backticks ```py\n```
        if content.startswith('```') and content.endswith('```'):
            if content[-4] == '\n':
                return '\n'.join(content.split('\n')[1:-1])
            return '\n'.join(content.split('\n')[1:]).rstrip('`')

        # Remove inline backticks `foo`
        return content.strip('` \n')

    @commands.command()
    async def ev(self, ctx:utils.Context, *, content:str):
        """Evaluates some Python code

        Gracefully stolen from Rapptz ->
        https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/admin.py#L72-L117"""

        # Make the environment
        env = {
            'bot': self.bot,
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message,
            'self': self,
        }
        env.update(globals())

        # Make code and output string
        content = self._cleanup_code(content)
        stdout = io.StringIO()
        to_compile = f'async def func():\n{textwrap.indent(content, "  ")}'

        # Make the function into existence
        try:
            exec(to_compile, env)
        except Exception as e:
            return await ctx.send(f'```py\n{e.__class__.__name__}: {e}\n```')

        # Grab the function we just made and run it
        func = env['func']
        try:
            # Shove stdout into StringIO
            with contextlib.redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            # Oh no it caused an error
            value = stdout.getvalue()
            await ctx.send(f'```py\n{value}{traceback.format_exc()}\n```')
        else:
            # Oh no it didn't cause an error
            value = stdout.getvalue()

            # Give reaction just to show that it ran
            await ctx.okay(ignore_error=True)

            # If the function returned nothing
            if ret is None:
                # It might have printed something
                if value:
                    await ctx.send(f'```py\n{value}\n```')

            # If the function did return a value
            else:
                self._last_result = ret
                text = f'```py\n{value}{ret}\n```'
                if len(text) > 2000:
                    return await ctx.send(file=discord.File(io.StringIO(value), filename='ev.txt'))
                await ctx.send(text)

    @commands.command(aliases=['rld'])
    async def reload(self, ctx:utils.Context, *cog_name:str):
        """Unloads and reloads a cog from the bot"""

        cog_name = 'cogs.' + '_'.join([i for i in cog_name])

        try:
            self.bot.load_extension(cog_name)
        except commands.ExtensionAlreadyLoaded:
            try:
                self.bot.unload_extension(cog_name)
                self.bot.load_extension(cog_name)
            except Exception:
                await ctx.send('```py\n' + traceback.format_exc() + '```')
                return
        except Exception:
            await ctx.send('```py\n' + traceback.format_exc() + '```')
            return
        await ctx.send('Cog reloaded.')

    @commands.command()
    async def runsql(self, ctx:utils.Context, *, content:str):
        """Runs a line of SQL into the sparcli database"""

        # Grab data
        async with self.bot.database() as db:
            data = await db(content) or 'No content.'

        # Single line output
        if type(data) in [str, type(None)]:
            await ctx.send(data)
            return

        # Get columns and widths
        column_headers = list(x[0].keys())
        column_max_lengths = {i:0 for i in column_headers}
        for row in data:
            for header in column_headers:
                column_max_lengths[header] = max(column_max_lengths[header], len(row[header]))

        # Sort our output
        output = []  # List of lines
        current_line = ""
        for row in [{i:i for i in column_headers}] + list(data):
            for header in column_headers:
                current_line += format(row[header], f"<{column_max_lengths[header]}") + '|'
            output.append(current_line.strip('| '))

        # Send it to user
        string_output = '\n'.join(output)
        await ctx.send('```\n{}```'.format(string_output))

    @commands.group()
    async def profile(self, ctx:utils.Context):
        """A parent group for the different bot profile commands"""

        pass

    @profile.command(aliases=['username'])
    async def name(self, ctx:utils.Context, *, username:str):
        """Lets you change the username of the bot"""

        if len(username) > 32:
            await ctx.send('That username is too long to be compatible with Discord.')
            return

        await self.bot.user.edit(username=username)
        await ctx.okay(ignore_error=True)

    @profile.command(aliases=['photo', 'image', 'avatar'])
    async def picture(self, ctx:utils.Context, *, image_url:str=None):
        """Lets you change the avatar of the bot"""

        # Get url
        if image_url == None:
            try:
                image_url = ctx.message.attachments[0].url
            except IndexError:
                await ctx.send("You need to provide an image.")
                return

        # Get image bytes
        async with self.bot.session.get(image_url) as r:
            image_content = await r.read()

        # Edit bot
        await self.bot.user.edit(avatar=image_content)
        await ctx.okay(ignore_error=True)

    @profile.command(aliases=['game'])
    async def activity(self, ctx:utils.Context, activity_type:str, *, name:str=None):
        """Changes the activity of the bot"""

        if name:
            activity = discord.Activity(name=name, type=getattr(discord.ActivityType, activity_type.lower()))
        else:
            return await self.bot.set_default_presence()
        await self.bot.change_presence(activity=activity, status=self.bot.guilds[0].me.status)

    @profile.command()
    async def status(self, ctx:utils.Context, status:str):
        """Changes the bot's status"""

        status_object = getattr(discord.Status, status.lower())
        await self.bot.change_presence(activity=self.bot.guilds[0].me.activity, status=status_object)

    @commands.command()
    async def sudo(self, ctx, who:utils.converters.UserID, *, command: str):
        """Run a command as another user optionally in another channel."""

        msg = copy.copy(ctx.message)
        msg.author = self.bot.get_user(who) or await self.bot.fetch_user(who)
        msg.content = ctx.prefix + command
        new_ctx = await self.bot.get_context(msg, cls=type(ctx))
        await self.bot.invoke(new_ctx)

    @commands.command()
    async def copyfamilytoguild(self, ctx:utils.Context, user:utils.converters.UserID, guild_id:int):
        """Copies a family's span to a given guild ID for server specific families"""

        # Get their current family
        tree = utils.FamilyTreeMember.get(user)
        users = tree.span(expand_upwards=True, add_parent=True)
        await ctx.channel.trigger_typing()

        # Database it to the new guild
        db = await self.bot.database.get_connection()

        # Delete current guild data
        await db('DELETE FROM marriages WHERE guild_id=$1', guild_id)
        await db('DELETE FROM parents WHERE guild_id=$1', guild_id)

        # Generate new data to copy
        parents = ((i.id, i._parent, guild_id) for i in users if i._parent)
        partners = ((i.id, i._partner, guild_id) for i in users if i._partner)

        # Push to db
        await db.conn.copy_records_to_table('parents', columns=['child_id', 'parent_id', 'guild_id'], records=parents)
        await db.conn.copy_records_to_table('marriages', columns=['user_id', 'partner_id', 'guild_id'], records=partners)

        # Send to user
        await ctx.send(f"Copied over `{len(users)}` users.")
        await db.disconnect()

    @commands.command()
    async def copyfamilytoguildnodelete(self, ctx:utils.Context, user:utils.converters.UserID, guild_id:int):
        """Copies a family's span to a given guild ID for server specific families"""

        # Get their current family
        tree = utils.FamilyTreeMember.get(user)
        users = tree.span(expand_upwards=True, add_parent=True)
        await ctx.channel.trigger_typing()

        # Database it to the new guild
        db = await self.bot.database.get_connection()

        # Generate new data to copy
        parents = ((i.id, i._parent, guild_id) for i in users if i._parent)
        partners = ((i.id, i._partner, guild_id) for i in users if i._partner)

        # Push to db
        try:
            await db.conn.copy_records_to_table('parents', columns=['child_id', 'parent_id', 'guild_id'], records=parents)
            await db.conn.copy_records_to_table('marriages', columns=['user_id', 'partner_id', 'guild_id'], records=partners)
        except Exception:
            await ctx.send("I encountered an error copying that family over.")
            return

        # Send to user
        await ctx.send(f"Copied over `{len(users)}` users.")
        await db.disconnect()

    @commands.command()
    async def addserverspecific(self, ctx:utils.Context, guild_id:int):
        """Adds a guild to the MarriageBot Gold whitelist"""

        async with self.bot.database() as db:
            await db('INSERT INTO guild_specific_families VALUES ($1)', guild_id)
        await ctx.okay(ignore_error=True)


def setup(bot:utils.CustomBot):
    x = OwnerOnly(bot)
    bot.add_cog(x)


