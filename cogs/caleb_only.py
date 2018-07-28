from traceback import format_exc
from asyncio import iscoroutine
from aiohttp import ClientSession
from discord import Member
from discord.ext.commands import command, Context, group
from cogs.utils.custom_bot import CustomBot
from cogs.utils.family_tree.family_tree_member import FamilyTreeMember


class CalebOnly(object):
    '''
    The parentage cog
    Handles the adoption of parents
    '''

    def __init__(self, bot:CustomBot):
        self.bot = bot
        self.last_tree = None

    async def __local_check(self, ctx:Context):
        return str(ctx.author) == 'Caleb#2831'


    @command(hidden=True)
    async def addallusers(self, ctx:Context):
        '''
        Adds all users to the family tree holder
        '''

        await ctx.send('Adding now...')
        async with self.bot.database() as db:
            partnerships = await db('SELECT * FROM marriages WHERE valid=TRUE')
            parents = await db('SELECT * FROM parents')
        for i in partnerships:
            FamilyTreeMember(discord_id=i['user_id'], children=[], parent_id=None, partner_id=i['partner_id'])
        for i in parents:
            parent = FamilyTreeMember.get(i['parent_id'])
            parent.children.append(i['child_id'])
            child = FamilyTreeMember.get(i['child_id'])
            child.parent = i['parent_id']
        await ctx.send('Done.')


    @command(hidden=True)
    async def ev(self, ctx:Context, *, content:str):
        '''
        Runs some text through Python's eval function
        '''

        try:
            ans = eval(content, globals(), locals())
        except Exception as e:
            await ctx.send('```py\n' + format_exc() + '```')
            return
        if iscoroutine(ans):
            ans = await ans
        await ctx.send('```py\n' + str(ans) + '```')


    @command(aliases=['rld'])
    async def reload(self, ctx:Context, *cog_name:str):
        '''
        Unloads a cog from the bot
        '''

        self.bot.unload_extension('cogs.' + '_'.join([i for i in cog_name]))
        try:
            self.bot.load_extension('cogs.' + '_'.join([i for i in cog_name]))
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
        


def setup(bot:CustomBot):
    x = CalebOnly(bot)
    bot.add_cog(x)


