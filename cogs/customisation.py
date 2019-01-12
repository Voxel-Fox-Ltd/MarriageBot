from discord.ext.commands import command, group, Context

from cogs.utils.custom_bot import CustomBot
from cogs.utils.customised_tree_user import CustomisedTreeUser
from cogs.utils.colour_dict import COLOURS


class Customisation(object):
    '''
    A set of commands that let you customise what your family tree looks like
    '''

    def __init__(self, bot:CustomBot):
        self.bot = bot


    async def coloursetter(self, ctx:Context, colour:str, attribute:str):
        '''
        Actually does all the heavy lifting for the colour setters
        '''

        tree = CustomisedTreeUser.get(ctx.author.id)
        if colour == None:
            if getattr(tree, attribute) == None:
                await ctx.send("You already have that set to the default colour.")
            else:
                setattr(tree, attribute, None)
                await ctx.send("Set to the default colour.")
            async with self.bot.database() as db:
                try:
                    await db(f'UPDATE customisation SET {attribute}=null WHERE user_id=$1', ctx.author.id)
                except Exception:
                    pass
            return 

        # Run through checks and make sure it's a real colour
        colour = colour.strip('#.')
        colour_by_name = COLOURS.get(colour.lower())
        if colour_by_name != None:
            hex_colour = colour_by_name
        else:
            if len(colour) != 6:
                await ctx.send("The colour you passed is not a valid colour name or hex code.") 
                return
            try:
                hex_colour = int(colour, 16)
            except ValueError:
                await ctx.send("The colour you passed is not a valid colour name or hex code.") 
                return

        # Valid colour, save
        async with self.bot.database() as db:
            try:
                await db(f'INSERT INTO customisation (user_id, {attribute}) VALUES ($1, $2)', ctx.author.id, hex_colour)
            except Exception:
                await db(f'UPDATE customisation SET {attribute}=$1 WHERE user_id=$2', hex_colour, ctx.author.id)

        setattr(tree, attribute, hex_colour)
        await ctx.send("Customisation saved.") 
        CustomisedTreeUser.all_users[ctx.author.id] = tree


    @group(aliases=['customize'])
    async def customise(self, ctx:Context):
        '''
        Allows you to change your tree colours. See "help customise".

        This is a command group - run the following with "customise [attribute] [colour]", eg "customise background red", or "customise node #ff0000".
        '''

        if not ctx.invoked_subcommand:
            await ctx.send(f"See `{ctx.prefix}help {ctx.command.name}` to see how to use this command properly.")
        else:
            return


    @customise.command(aliases=['line', 'lines', 'edges'])
    async def edge(self, ctx:Context, *, colour:str=None):
        '''
        Changes the colour of the lines linking users
        '''
        
        await self.coloursetter(ctx, colour, 'edge')


    @customise.command(aliases=['user', 'person'])
    async def node(self, ctx:Context, *, colour:str=None):
        '''
        Changes the colour of users
        '''
        
        await self.coloursetter(ctx, colour, 'node')


    @customise.command(aliases=['fontcolour', 'fontcolor'])
    async def font(self, ctx:Context, *, colour:str=None):
        '''
        Changes the colour of the font
        '''
        
        await self.coloursetter(ctx, colour, 'font')


    @customise.command(aliases=['highlightedfont', 'highfont', 'highlightfont'])
    async def hfont(self, ctx:Context, *, colour:str=None):
        '''
        Chagnes the colour of the highlighted user's font
        '''
        
        await self.coloursetter(ctx, colour, 'highlighted_font')


    @customise.command(aliases=['highlightednode', 'highnode', 'highlightnode', 'highlightedperson', 'highperson', 'highlightperson', 'highlighteduser', 'highuser', 'highlightuser'])
    async def hnode(self, ctx:Context, *, colour:str=None):
        '''
        Changes the colour of the highlighted user's node
        '''
        
        await self.coloursetter(ctx, colour, 'highlighted_node')


    @customise.command(aliases=['background', 'BG'])
    async def bg(self, ctx:Context, *, colour:str=None):
        '''
        Changes the colour of the background of the tree
        '''

        await self.coloursetter(ctx, colour, 'background')


def setup(bot:CustomBot):
    x = Customisation(bot)
    bot.add_cog(x)
