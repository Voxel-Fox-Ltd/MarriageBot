from traceback import format_exc
from io import StringIO
from textwrap import indent
from contextlib import redirect_stdout
import copy
import collections

import discord
from discord.ext import commands

from cogs import utils


class OwnerOnly(utils.Cog):
    """Handles commands that only the owner should be able to run"""

    async def cog_check(self, ctx:utils.Context):
        """Local check for the cog - make sure the person running the command is an owner"""

        if ctx.author.id in self.bot.config['owners']:
            return True
        raise commands.NotOwner

    @commands.command(aliases=['pm', 'dm'], cls=utils.Command)
    async def message(self, ctx:utils.Context, user:discord.User, *, content:str):
        """PMs a user the given content"""

        await user.send(content)

    def cleanup_code(self, content):
        """Automatically removes code blocks from the code."""

        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            if content[-4] == '\n':
                return '\n'.join(content.split('\n')[1:-1])
            return '\n'.join(content.split('\n')[1:]).rstrip('`')

        # remove `foo`
        return content.strip('` \n')

    @commands.command(cls=utils.Command)
    async def ev(self, ctx:utils.Context, *, content:str):
        """
        Evaluates some Python code

        Gratefully stolen from Rapptz ->
        https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/admin.py#L72-L117
        """

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
        content = self.cleanup_code(content)
        stdout = StringIO()
        to_compile = f'async def func():\n{indent(content, "  ")}'

        # Make the function into existence
        try:
            exec(to_compile, env)
        except Exception as e:
            return await ctx.send(f'```py\n{e.__class__.__name__}: {e}\n```')

        # Grab the function we just made and run it
        func = env['func']
        try:
            # Shove stdout into StringIO
            with redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            # Oh no it caused an error
            value = stdout.getvalue()
            await ctx.send(f'```py\n{value}{format_exc()}\n```')
        else:
            # Oh no it didn't cause an error
            value = stdout.getvalue()

            # Give reaction just to show that it ran
            try:
                await ctx.message.add_reaction('\u2705')
            except:
                pass

            # If the function returned nothing
            if ret is None:
                # It might have printed something
                if value:
                    await ctx.send(f'```py\n{value}\n```')

            # If the function did return a value
            else:
                text = f'```py\n{value}{ret}\n```'
                if len(text) > 2000:
                    return await ctx.send(file=discord.File(StringIO('\n'.join(text.split('\n')[1:-1])), filename='ev.txt'))
                await ctx.send(text)

    @commands.command(aliases=['rld'], cls=utils.Command)
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
                await ctx.send('```py\n' + format_exc() + '```')
                return
        except Exception:
            await ctx.send('```py\n' + format_exc() + '```')
            return
        await ctx.send('Cog reloaded.')

    @commands.command(cls=utils.Command)
    async def runsql(self, ctx:utils.Context, *, content:str):
        """Throws some SQL into the database handler"""

        # Run SQL
        async with self.bot.database() as db:
            data = await db(content)

        # Give reaction just to show that it ran
        try:
            await ctx.message.add_reaction('\u2705')
        except:
            if data is None:
                return await ctx.send("No content.")
        if data is None:
            return

        # Set up our column groups
        column_headers = list(data[0].keys())
        column_length = collections.defaultdict(int)
        column_data = collections.defaultdict(list)

        # Work out what goes in our columns
        for row in data:
            for row_header, row_data in row.items():
                column_length[row_header] = max([column_length[row_header], len(data), len(row_header)])
                column_data[row_header].append(row_data)

        # Build our output
        output_lines = ['|'.join([format(i, f"<{column_length[i]}") for i in column_headers])]  # Set up headers
        output_lines.append('|'.join([column_length[i] * '-' for i in column_headers]))  # Set up header divider
        for index in range(len(column_data[column_headers[0]])):
            line_builder = []
            for header in column_headers:
                line = column_data[header][index]
                line_builder.append(format(line, f"<{column_length[header]}"))
            output_lines.append('|'.join(line_builder))

        # Send to user
        value = '\n'.join(output_lines)
        text = f'```py\n{value}\n```'
        if len(text) > 2000:
            return await ctx.send(file=discord.File(StringIO(value), filename='runsql.txt'))
        await ctx.send(text)

    @commands.group(cls=utils.Group)
    async def profile(self, ctx:utils.Context):
        """A parent command for the profile section"""

        pass

    @profile.command(aliases=['username'], cls=utils.Command)
    async def name(self, ctx:utils.Context, *, username:str):
        """Lets you set the username for the bot account"""

        if len(username) > 32:
            return await ctx.send('That username is too long.')
        await self.bot.user.edit(username=username)
        await ctx.send('Done.')

    @profile.command(aliases=['photo', 'image', 'avatar'], cls=utils.Command)
    async def picture(self, ctx:utils.Context, *, image_url:str=None):
        """Lets you set the profile picture of the bot"""

        if image_url == None:
            try:
                image_url = ctx.message.attachments[0].url
            except IndexError:
                return await ctx.send("You need to provide an image.")

        async with self.bot.session.get(image_url) as r:
            image_content = await r.read()
        await self.bot.user.edit(avatar=image_content)
        await ctx.send('Done.')

    @profile.command(aliases=['game'], cls=utils.Command)
    async def activity(self, ctx:utils.Context, activity_type:str, *, name:str=None):
        """Changes the activity of the bot"""

        if name:
            activity = discord.Activity(name=name, type=getattr(discord.ActivityType, activity_type.lower()))
        else:
            return await self.bot.set_default_presence()
        await self.bot.change_presence(activity=activity, status=self.bot.guilds[0].me.status)

    @profile.command(cls=utils.Command)
    async def status(self, ctx:utils.Context, status:str):
        """Changes the online status of the bot"""

        status_o = getattr(discord.Status, status.lower())
        await self.bot.change_presence(activity=self.bot.guilds[0].me.activity, status=status_o)

    @commands.command(cls=utils.Command)
    async def sudo(self, ctx, who:discord.User, *, command: str):
        """Run a command as another user optionally in another channel."""

        msg = copy.copy(ctx.message)
        msg.author = ctx.guild.get_member(who.id) or who
        msg.content = ctx.prefix + command
        new_ctx = await self.bot.get_context(msg, cls=type(ctx))
        await self.bot.invoke(new_ctx)


def setup(bot:utils.CustomBot):
    x = OwnerOnly(bot)
    bot.add_cog(x)
