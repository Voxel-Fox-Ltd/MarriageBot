from traceback import format_exc
from asyncio import iscoroutine, wait_for
from io import StringIO 
from textwrap import indent
from contextlib import redirect_stdout

from aiohttp import ClientSession
from discord import Member, Message, Activity, ActivityType, User, Status, Embed
from discord.ext.commands import command, Context, group, NotOwner, Cog, CommandOnCooldown, ExtensionAlreadyLoaded
from pympler import summary, muppy

from cogs.utils.custom_bot import CustomBot
from cogs.utils.family_tree.family_tree_member import FamilyTreeMember
from cogs.utils.customised_tree_user import CustomisedTreeUser


class CalebOnly(Cog):
    '''
    The parentage cog
    Handles the adoption of parents
    '''

    def __init__(self, bot:CustomBot):
        self.bot = bot
        self._last_result = None


    async def cog_command_error(self, ctx:Context, error):
        '''
        Local error handler for the cog
        '''

        # Throw errors properly for me
        if ctx.author.id in self.bot.config['owners'] and not isinstance(error, CommandOnCooldown):
            text = f'```py\n{error}```'
            await ctx.send(text)
            raise error


    async def cog_check(self, ctx:Context):
        if ctx.author.id in self.bot.config['owners']:
            return True
        raise NotOwner


    @command(aliases=['pm', 'dm'])
    async def message(self, ctx:Context, user:User, *, content:str):
        '''
        Messages a user the given content
        '''

        await user.send(content)


    @command()
    async def seememory(self, ctx:Context):
        '''
        Shows you the number of each created object in the program
        '''

        # summary.print_(summary.summarize(muppy.get_objects()))

        awaitable_dot_code = self.bot.loop.run_in_executor(None, muppy.get_objects)
        try:
            objects = await wait_for(awaitable_dot_code, timeout=10.0, loop=self.bot.loop)
        except Exception as e:
            await ctx.send(f"{e!s}")
            return
        summary.print_(summary.summarize(objects))
        await ctx.send("Printed to console.")


    def cleanup_code(self, content):
        """Automatically removes code blocks from the code."""

        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            if content[-4] == '\n':
                return '\n'.join(content.split('\n')[1:-1])
            return '\n'.join(content.split('\n')[1:]).rstrip('`')

        # remove `foo`
        return content.strip('` \n')


    @command()
    async def ev(self, ctx:Context, *, content:str):
        '''
        Evaluates some Python code

        Gracefully stolen from Rapptz -> 
        https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/admin.py#L72-L117
        '''

        # Make the environment
        env = {
            'bot': self.bot,
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message,
            '_': self._last_result,
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
                self._last_result = ret
                await ctx.send(f'```py\n{value}{ret}\n```')


    @command(aliases=['rld'])
    async def reload(self, ctx:Context, *cog_name:str):
        '''
        Unloads a cog from the bot
        '''

        cog_name = 'cogs.' + '_'.join([i for i in cog_name])

        try:
            self.bot.load_extension(cog_name)
        except ExtensionAlreadyLoaded:
            try:
                self.bot.reload_extension(cog_name)
            except Exception as e:
                await ctx.send('```py\n' + format_exc() + '```')
                return
        except Exception as e:
            await ctx.send('```py\n' + format_exc() + '```')
            return
        await ctx.send('Cog reloaded.')


    @command()
    async def runsql(self, ctx:Context, *, content:str):
        '''
        Runs a line of SQL into the sparcli database
        '''

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


    @group()
    async def profile(self, ctx:Context):
        '''
        A parent group for the different profile commands
        '''

        pass


    @profile.command(aliases=['username'])
    async def name(self, ctx:Context, *, username:str):
        '''
        Lets you change the username of the bot
        '''

        if len(username) > 32:
            await ctx.send('That username is too long to be compatible with Discord.')
            return 

        await self.bot.user.edit(username=username)
        await ctx.send('Done.')


    @profile.command(aliases=['photo', 'image', 'avatar'])
    async def picture(self, ctx:Context, *, image_url:str=None):
        '''
        Lets you change the username of the bot
        '''

        if image_url == None:
            try:
                image_url = ctx.message.attachments[0].url 
            except IndexError:
                await ctx.send("You need to provide an image.")
                return

        async with ClientSession(loop=self.bot.loop) as session:
            async with session.get(image_url) as r:
                image_content = await r.read()
        await self.bot.user.edit(avatar=image_content)
        await ctx.send('Done.')


    @profile.command(aliases=['game'])
    async def activity(self, ctx:Context, activity_type:str, *, name:str=None):
        '''
        Changes the activity of the bot
        '''

        if name:
            activity = Activity(name=name, type=getattr(ActivityType, activity_type.lower()))
        else:
            await self.bot.set_default_presence()
            return
        await self.bot.change_presence(activity=activity, status=self.bot.guilds[0].me.status)


    @profile.command()
    async def status(self, ctx:Context, status:str):
        '''
        Changes the bot's status
        '''

        status_o = getattr(Status, status.lower())
        await self.bot.change_presence(activity=self.bot.guilds[0].me.activity, status=status_o)


def setup(bot:CustomBot):
    x = CalebOnly(bot)
    bot.add_cog(x)


