from traceback import format_exc
from asyncio import iscoroutine, wait_for
from io import StringIO
from textwrap import indent
from contextlib import redirect_stdout
import copy

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

    @commands.command(aliases=['pm', 'dm'], hidden=True)
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

    @commands.command(hidden=True)
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

    @commands.command(aliases=['rld'], hidden=True)
    async def reload(self, ctx:utils.Context, *cog_name:str):
        """Unloads and reloads a cog from the bot"""

        cog_name = 'cogs.' + '_'.join([i for i in cog_name])

        try:
            self.bot.load_extension(cog_name)
        except commands.ExtensionAlreadyLoaded:
            try:
                self.bot.unload_extension(cog_name)
                self.bot.load_extension(cog_name)
            except Exception as e:
                await ctx.send('```py\n' + format_exc() + '```')
                return
        except Exception as e:
            await ctx.send('```py\n' + format_exc() + '```')
            return
        await ctx.send('Cog reloaded.')

    @commands.command(hidden=True)
    async def runsql(self, ctx:utils.Context, *, content:str):
        """Throws some SQL into the database handler"""

        async with self.bot.database() as db:
            x = await db(content) or 'No content.'
        if type(x) in [str, type(None)]:
            await ctx.send(x)
            return

        # Get the results into groups
        column_headers = list(x[0].keys())
        grouped_outputs = {}
        for i in column_headers:
            grouped_outputs[i] = []
        for guild_data in x:
            for i, o in guild_data.items():
                grouped_outputs[i].append(str(o))

        # Everything is now grouped super nicely
        # Now to get the maximum length of each column and add it as the last item
        for key, item_list in grouped_outputs.items():
            max_len = max([len(i) for i in item_list + [key]])
            grouped_outputs[key].append(max_len)

        # Format the outputs and add to a list
        key_headers = []
        temp_output = []
        for key, value in grouped_outputs.items():
            # value is a list of unformatted strings
            key_headers.append(format(key, '<' + str(value[-1])))
            formatted_values = [format(i, '<' + str(value[-1])) for i in value[:-1]]
            # string_value = '|'.join(formatted_values)
            temp_output.append(formatted_values)
        key_string = '|'.join(key_headers)

        # Rotate the list because apparently I need to
        output = []
        for i in range(len(temp_output[0])):
            temp = []
            for o in temp_output:
                temp.append(o[i])
            output.append('|'.join(temp))

        # Add some final values before returning to the user
        line = '-' * len(key_string)
        output = [key_string, line] + output
        string_output = '\n'.join(output)
        await ctx.send('```\n{}```'.format(string_output))

    @commands.group(hidden=True)
    async def profile(self, ctx:utils.Context):
        """A parent command for the profile section"""

        pass

    @profile.command(aliases=['username'], hidden=True)
    async def name(self, ctx:utils.Context, *, username:str):
        """Lets you set the username for the bot account"""

        if len(username) > 32:
            await ctx.send('That username is too long.')
            return
        await self.bot.user.edit(username=username)
        await ctx.send('Done.')

    @profile.command(aliases=['photo', 'image', 'avatar'], hidden=True)
    async def picture(self, ctx:utils.Context, *, image_url:str=None):
        """Lets you set the profile picture of the bot"""

        if image_url == None:
            try:
                image_url = ctx.message.attachments[0].url
            except IndexError:
                await ctx.send("You need to provide an image.")
                return

        async with self.bot.session.get(image_url) as r:
            image_content = await r.read()
        await self.bot.user.edit(avatar=image_content)
        await ctx.send('Done.')

    @profile.command(aliases=['game'], hidden=True)
    async def activity(self, ctx:utils.Context, activity_type:str, *, name:str=None):
        """Changes the activity of the bot"""

        if name:
            activity = discord.Activity(name=name, type=getattr(discord.ActivityType, activity_type.lower()))
        else:
            await self.bot.set_default_presence()
            return
        await self.bot.change_presence(activity=activity, status=self.bot.guilds[0].me.status)

    @profile.command(hidden=True)
    async def status(self, ctx:utils.Context, status:str):
        """Changes the online status of the bot"""

        status_o = getattr(discord.Status, status.lower())
        await self.bot.change_presence(activity=self.bot.guilds[0].me.activity, status=status_o)

    @commands.command(hidden=True)
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
