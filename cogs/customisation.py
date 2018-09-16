from discord.ext.commands import command, group, Context
from cogs.utils.custom_bot import CustomBot
from cogs.utils.customised_tree_user import CustomisedTreeUser


class Customisation(object):
    '''
    A set of commands that let you customise what your family tree looks like
    '''

    def __init__(self, bot:CustomBot):
        self.bot = bot


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
    async def edge(self, ctx:Context, colour:str=None):
        '''
        Changes the colour of the lines linking users
        '''
        
        tree = CustomisedTreeUser.get(ctx.author.id)
        if colour == None:
            if tree.edge == None:
                await ctx.send("You already have that set to the default colour.")
                return 
            tree.edge = None 
            await ctx.send("Set to the default colour.")
            return 

        # Run through checks and make sure it's a real colour
        colour = colour.strip('#')
        if len(colour) != 6:
            await ctx.send("This command only accepts a valid hex code.") 
            return
        try:
            hex_colour = int(colour, 16)
        except ValueError:
            await ctx.send("This command only accepts a valid hex code.") 
            return

        # Valid colour, save
        async with self.bot.database() as db:
            try:
                await db('INSERT INTO customisation (user_id) VALUES ($1)', ctx.author.id)
            except Exception:
                pass
            await db('UPDATE customisation SET edge=$1 WHERE user_id=$2', hex_colour, ctx.author.id)
        tree.edge = hex_colour
        await ctx.send("Customisation saved.") 
        CustomisedTreeUser.all_users[ctx.author.id] = tree


    @customise.command(aliases=['user', 'person'])
    async def node(self, ctx:Context, colour:str=None):
        '''
        Changes the colour of users
        '''
        
        tree = CustomisedTreeUser.get(ctx.author.id)
        if colour == None:
            if tree.node == None:
                await ctx.send("You already have that set to the default colour.")
                return 
            tree.node = None 
            await ctx.send("Set to the default colour.")
            return 

        # Run through checks and make sure it's a real colour
        colour = colour.strip('#')
        if len(colour) != 6:
            await ctx.send("This command only accepts a valid hex code.") 
            return
        try:
            hex_colour = int(colour, 16)
        except ValueError:
            await ctx.send("This command only accepts a valid hex code.") 
            return

        # Valid colour, save
        async with self.bot.database() as db:
            try:
                await db('INSERT INTO customisation (user_id) VALUES ($1)', ctx.author.id)
            except Exception:
                pass
            await db('UPDATE customisation SET node=$1 WHERE user_id=$2', hex_colour, ctx.author.id)
        tree.node = hex_colour
        await ctx.send("Customisation saved.") 
        CustomisedTreeUser.all_users[ctx.author.id] = tree


    @customise.command(aliases=['fontcolour', 'fontcolor'])
    async def font(self, ctx:Context, colour:str=None):
        '''
        Changes the colour of the font
        '''
        
        tree = CustomisedTreeUser.get(ctx.author.id)
        if colour == None:
            if tree.font == None:
                await ctx.send("You already have that set to the default colour.")
                return 
            tree.font = None 
            await ctx.send("Set to the default colour.")
            return 

        # Run through checks and make sure it's a real colour
        colour = colour.strip('#')
        if len(colour) != 6:
            await ctx.send("This command only accepts a valid hex code.") 
            return
        try:
            hex_colour = int(colour, 16)
        except ValueError:
            await ctx.send("This command only accepts a valid hex code.") 
            return

        # Valid colour, save
        async with self.bot.database() as db:
            try:
                await db('INSERT INTO customisation (user_id) VALUES ($1)', ctx.author.id)
            except Exception:
                pass
            await db('UPDATE customisation SET font=$1 WHERE user_id=$2', hex_colour, ctx.author.id)
        tree.font = hex_colour
        await ctx.send("Customisation saved.") 
        CustomisedTreeUser.all_users[ctx.author.id] = tree


    @customise.command(aliases=['highlightedfont', 'highfont', 'highlightfont'])
    async def hfont(self, ctx:Context, colour:str=None):
        '''
        Chagnes the colour of the highlighted user's font
        '''
        
        tree = CustomisedTreeUser.get(ctx.author.id)
        if colour == None:
            if tree.highlighted_font == None:
                await ctx.send("You already have that set to the default colour.")
                return 
            tree.highlighted_font = None 
            await ctx.send("Set to the default colour.")
            return 

        # Run through checks and make sure it's a real colour
        colour = colour.strip('#')
        if len(colour) != 6:
            await ctx.send("This command only accepts a valid hex code.") 
            return
        try:
            hex_colour = int(colour, 16)
        except ValueError:
            await ctx.send("This command only accepts a valid hex code.") 
            return

        # Valid colour, save
        async with self.bot.database() as db:
            try:
                await db('INSERT INTO customisation (user_id) VALUES ($1)', ctx.author.id)
            except Exception:
                pass
            await db('UPDATE customisation SET highlighted_font=$1 WHERE user_id=$2', hex_colour, ctx.author.id)
        tree.highlighted_font = hex_colour
        await ctx.send("Customisation saved.") 
        CustomisedTreeUser.all_users[ctx.author.id] = tree


    @customise.command(aliases=['highlightednode', 'highnode', 'highlightnode', 'highlightedperson', 'highperson', 'highlightperson', 'highlighteduser', 'highuser', 'highlightuser'])
    async def hnode(self, ctx:Context, colour:str=None):
        '''
        Changes the colour of the highlighted user's node
        '''
        
        tree = CustomisedTreeUser.get(ctx.author.id)
        if colour == None:
            if tree.highlighted_node == None:
                await ctx.send("You already have that set to the default colour.")
                return 
            tree.highlighted_node = None 
            await ctx.send("Set to the default colour.")
            return 

        # Run through checks and make sure it's a real colour
        colour = colour.strip('#')
        if len(colour) != 6:
            await ctx.send("This command only accepts a valid hex code.") 
            return
        try:
            hex_colour = int(colour, 16)
        except ValueError:
            await ctx.send("This command only accepts a valid hex code.") 
            return

        # Valid colour, save
        async with self.bot.database() as db:
            try:
                await db('INSERT INTO customisation (user_id) VALUES ($1)', ctx.author.id)
            except Exception:
                pass
            await db('UPDATE customisation SET highlighted_node=$1 WHERE user_id=$2', hex_colour, ctx.author.id)
        tree.highlighted_node = hex_colour
        await ctx.send("Customisation saved.") 
        CustomisedTreeUser.all_users[ctx.author.id] = tree


    @customise.command(aliases=['background'])
    async def bg(self, ctx:Context, colour:str=None):
        '''
        Changes the colour of the background of the tree
        '''
        tree = CustomisedTreeUser.get(ctx.author.id)
        if colour == None:
            if tree.background == None:
                await ctx.send("You already have that set to the default colour.")
                return 
            tree.background = None 
            await ctx.send("Set to the default colour.")
            return 

        # Run through checks and make sure it's a real colour
        colour = colour.strip('#')
        if len(colour) != 6:
            await ctx.send("This command only accepts a valid hex code.") 
            return
        try:
            hex_colour = int(colour, 16)
        except ValueError:
            await ctx.send("This command only accepts a valid hex code.") 
            return

        # Valid colour, save
        async with self.bot.database() as db:
            try:
                await db('INSERT INTO customisation (user_id) VALUES ($1)', ctx.author.id)
            except Exception:
                pass
            await db('UPDATE customisation SET background=$1 WHERE user_id=$2', hex_colour, ctx.author.id)
        tree.background = hex_colour
        await ctx.send("Customisation saved.") 
        CustomisedTreeUser.all_users[ctx.author.id] = tree


def setup(bot:CustomBot):
    x = Customisation(bot)
    bot.add_cog(x)
