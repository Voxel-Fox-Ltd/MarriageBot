import contextlib
import copy
import io
import json
import textwrap
import traceback

import discord
from discord.ext import commands

from cogs import utils


class OwnerOnly(utils.Cog):
    """Handles commands that only the owner should be able to run"""

    @commands.command(aliases=['pm', 'dm'], cls=utils.Command)
    @commands.is_owner()
    async def message(self, ctx:utils.Context, user:discord.User, *, content:str):
        """PMs a user the given content"""

        await user.send(content)

    def _cleanup_code(self, content):
        """Automatically removes code blocks from the code."""

        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            if content[-4] == '\n':
                return '\n'.join(content.split('\n')[1:-1])
            return '\n'.join(content.split('\n')[1:]).rstrip('`')

        # remove `foo`
        return content.strip('` \n')

    @commands.command(aliases=['evall'], cls=utils.Command)
    @commands.is_owner()
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
        code = f'async def func():\n{textwrap.indent(content, "  ")}'

        # Make the function into existence
        stdout = io.StringIO()
        try:
            exec(code, env)
        except Exception as e:
            return await ctx.send(f'```py\n{e.__class__.__name__}: {e}\n```')

        # Grab the function we just made and run it
        func = env['func']
        try:
            # Shove stdout into StringIO
            with contextlib.redirect_stdout(stdout):
                ret = await func()
        except Exception:
            # Oh no it caused an error
            value = stdout.getvalue()
            await ctx.send(f'```py\n{value}{traceback.format_exc()}\n```')
        else:
            # Oh no it didn't cause an error
            value = stdout.getvalue()

            # Give reaction just to show that it ran
            await ctx.message.add_reaction("\N{OK HAND SIGN}")

            # If the function returned nothing
            if ret is None:
                # It might have printed something
                if value:
                    await ctx.send(f'```py\n{value}\n```')

            # If the function did return a value
            else:
                self._last_result = ret
                result_raw = ret or value
                result = str(result_raw)
                if type(result_raw) == dict:
                    try:
                        result = json.dumps(result_raw, indent=4)
                    except Exception:
                        pass
                if type(result_raw) == dict and type(result) == str:
                    text = f'```json\n{result}\n```'
                else:
                    text = f'```py\n{result}\n```'
                if len(text) > 2000:
                    await ctx.send(file=discord.File(io.StringIO(result), filename='ev.txt'))
                else:
                    await ctx.send(text)

    @commands.command(aliases=['rld'], cls=utils.Command)
    @commands.is_owner()
    async def reload(self, ctx:utils.Context, *cog_name:str):
        """Unloads and reloads a cog from the bot"""

        cog_name = 'cogs.' + '_'.join([i for i in cog_name])

        try:
            self.bot.load_extension(cog_name)
        except commands.ExtensionAlreadyLoaded:
            try:
                # self.bot.unload_extension(cog_name)
                # self.bot.load_extension(cog_name)
                self.bot.reload_extension(cog_name)
            except Exception:
                await ctx.send('```py\n' + traceback.format_exc() + '```')
                return
        except Exception:
            await ctx.send('```py\n' + traceback.format_exc() + '```')
            return
        await ctx.send('Cog reloaded.')

    @commands.command(cls=utils.Command)
    @commands.is_owner()
    async def runsql(self, ctx:utils.Context, *, content:str):
        """Runs a line of SQL into the sparcli database"""

        # Grab data
        async with self.bot.database() as db:
            database_data = await db(content) or 'No content.'

        # Single line output
        if type(database_data) in [str, type(None)]:
            await ctx.send(database_data)
            return

        # Get columns and widths
        column_headers = list(database_data[0].keys())
        column_max_lengths = {i:0 for i in column_headers}
        for row in database_data:
            for header in column_headers:
                column_max_lengths[header] = max(column_max_lengths[header], len(str(row[header])))

        # Sort our output
        output = []  # List of lines
        current_line = ""
        for row in [{i:i for i in column_headers}] + list(database_data):
            for header in column_headers:
                current_line += format(str(row[header]), f"<{column_max_lengths[header]}") + '|'
            output.append(current_line.strip('| '))

        # Send it to user
        string_output = '\n'.join(output)
        await ctx.send('```\n{}```'.format(string_output))

    @commands.group(cls=utils.Group)
    @commands.is_owner()
    async def botuser(self, ctx:utils.Context):
        """A parent command for the bot user configuration section"""

        pass

    @botuser.command(aliases=['username'], cls=utils.Command)
    @commands.is_owner()
    async def name(self, ctx:utils.Context, *, username:str):
        """Lets you set the username for the bot account"""

        if len(username) > 32:
            return await ctx.send('That username is too long.')
        await self.bot.user.edit(username=username)
        await ctx.send('Done.')

    @botuser.command(aliases=['photo', 'image', 'avatar'], cls=utils.Command)
    @commands.is_owner()
    async def picture(self, ctx:utils.Context, *, image_url:str=None):
        """Lets you set the profile picture of the bot"""

        if image_url is None:
            try:
                image_url = ctx.message.attachments[0].url
            except IndexError:
                return await ctx.send("You need to provide an image.")

        async with self.bot.session.get(image_url) as r:
            image_content = await r.read()
        await self.bot.user.edit(avatar=image_content)
        await ctx.send('Done.')

    @botuser.command(aliases=['game'], cls=utils.Command)
    @commands.is_owner()
    async def activity(self, ctx:utils.Context, activity_type:str, *, name:str=None):
        """Changes the activity of the bot"""

        if name:
            activity = discord.Activity(name=name, type=getattr(discord.ActivityType, activity_type.lower()))
        else:
            return await self.bot.set_default_presence()
        await self.bot.change_presence(activity=activity, status=self.bot.guilds[0].me.status)

    @botuser.command(cls=utils.Command)
    @commands.is_owner()
    async def status(self, ctx:utils.Context, status:str):
        """Changes the online status of the bot"""

        status_o = getattr(discord.Status, status.lower())
        await self.bot.change_presence(activity=self.bot.guilds[0].me.activity, status=status_o)

    @commands.command(cls=utils.Command)
    @commands.is_owner()
    async def sudo(self, ctx, who:discord.User, *, command: str):
        """Run a command as another user optionally in another channel."""

        msg = copy.copy(ctx.message)
        msg.author = ctx.guild.get_member(who.id) or who
        msg.content = ctx.prefix + command
        new_ctx = await self.bot.get_context(msg, cls=type(ctx))
        await self.bot.invoke(new_ctx)

    @commands.command(cls=utils.Command)
    @commands.is_owner()
    async def addreaction(self, ctx, message:discord.Message, reaction:str):
        """Adds a reaction to a message"""

        await message.add_reaction(reaction)
        await ctx.message.add_reaction("\N{OK HAND SIGN}")


def setup(bot:utils.Bot):
    x = OwnerOnly(bot)
    bot.add_cog(x)
