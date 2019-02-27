from re import compile
from asyncio import TimeoutError as AsyncTimeoutError, wait_for

from discord import Member
from discord.ext.commands import command, Context, Cog, cooldown
from discord.ext.commands import MissingRequiredArgument, CommandOnCooldown, BadArgument
from discord.ext.commands.cooldowns import BucketType

from cogs.utils.custom_bot import CustomBot
from cogs.utils.family_tree.family_tree_member import FamilyTreeMember



class Marriage(Cog):
    '''
    The marriage cog
    Handles all marriage/divorce/etc commands
    '''

    def __init__(self, bot:CustomBot):
        self.bot = bot

        # Proposal text
        self.proposal_yes = compile(r"(i do)|(yes)|(of course)|(definitely)|(absolutely)|(yeah)|(yea)|(sure)|(accept)")
        self.proposal_no = compile(r"(i don't)|(i dont)|(no)|(to think)|(i'm sorry)|(im sorry)")


    async def cog_command_error(self, ctx:Context, error):
        '''
        Local error handler for the cog
        '''

        # Throw errors properly for me
        if ctx.author.id in self.bot.config['owners']:
            text = f'```py\n{error}```'
            await ctx.send(text)
            raise error

        # Missing argument
        if isinstance(error, MissingRequiredArgument):
            await ctx.send("You need to specify a person for this command to work properly.")
            return

        # Cooldown
        elif isinstance(error, CommandOnCooldown):
            if ctx.author.id in self.bot.config['owners']:
                await ctx.reinvoke()
            else:
                await ctx.send(f"You can only use this command once every `{error.cooldown.per:.0f} seconds` per server. You may use this again in `{error.retry_after:.2f} seconds`.")
            return
    
        # Argument conversion error
        elif isinstance(error, BadArgument):
            argument_text = self.bot.bad_argument.search(str(error)).group(2)
            await ctx.send(f"User `{argument_text}` could not be found.")
            return


    @command(aliases=['marry'])
    @cooldown(1, 5, BucketType.user)
    async def propose(self, ctx:Context, user:Member):
        '''
        Lets you propose to another Discord user
        '''

        instigator = ctx.author
        target = user  # Just so "target" didn't show up in the help message

        # See if either user is already being proposed to
        if instigator.id in self.bot.proposal_cache:
            x = self.bot.proposal_cache.get(instigator.id)
            if x[0] == 'INSTIGATOR':
                await ctx.send(self.bot.get_cog('ProposeRandomText').proposing_while_instigator(instigator, target))
            elif x[0] == 'TARGET':
                await ctx.send(self.bot.get_cog('ProposeRandomText').proposing_while_target(instigator, target))
            return
        elif target.id in self.bot.proposal_cache:
            x = self.bot.proposal_cache.get(target.id)
            if x[0] == 'INSTIGATOR':
                await ctx.send(self.bot.get_cog('ProposeRandomText').proposing_to_instigator(instigator, target))
            elif x[0] == 'TARGET':
                await ctx.send(self.bot.get_cog('ProposeRandomText').proposing_to_target(instigator, target))
            return

        # Manage exclusions
        if target.id == self.bot.user.id:
            await ctx.send(self.bot.get_cog('ProposeRandomText').proposing_to_me(instigator, target))
            return
        elif target.bot or instigator.bot:
            await ctx.send(self.bot.get_cog('ProposeRandomText').proposing_to_bot(instigator, target))
            return
        elif instigator.id == target.id:
            await ctx.send(self.bot.get_cog('ProposeRandomText').proposing_to_themselves(instigator, target))
            return

        # See if they're married or in the family already
        await ctx.trigger_typing()
        user_tree = FamilyTreeMember.get(instigator.id)

        # Make get_root awaitable 
        awaitable_root = self.bot.loop.run_in_executor(None, user_tree.get_root)
        try:
            root = await wait_for(awaitable_root, timeout=10.0, loop=self.bot.loop)
        except AsyncTimeoutError:
            await ctx.send("The `get_root` method for your family tree has failed. This is usually due to a loop somewhere in your tree.")
            return
        tree_id_list = [i.id for i in root.span(add_parent=True, expand_upwards=True)]

        if target.id in tree_id_list:
            await ctx.send(self.bot.get_cog('ProposeRandomText').proposing_to_family(instigator, target))
            return
        if user_tree.partner:
            await ctx.send(self.bot.get_cog('ProposeRandomText').proposing_when_married(instigator, target))
            return
        elif FamilyTreeMember.get(target.id).partner:
            await ctx.send(self.bot.get_cog('ProposeRandomText').proposing_to_married(instigator, target))
            return

        # Neither are married, set up the proposal
        await ctx.send(self.bot.get_cog('ProposeRandomText').valid_proposal(instigator, target))
        self.bot.proposal_cache[instigator.id] = ('INSTIGATOR', 'MARRIAGE')
        self.bot.proposal_cache[target.id] = ('TARGET', 'MARRIAGE')

        # Make the check
        def check(message):
            '''
            The check to make sure that the user is giving a valid yes/no
            when provided with a proposal
            '''
            
            if message.author.id != target.id:
                return False
            if message.channel.id != ctx.channel.id:
                return False
            c = message.content.casefold()
            if not c:
                return False
            no = self.proposal_no.search(c)
            yes = self.proposal_yes.search(c)
            if any([yes, no]):
                return 'NO' if no else 'YES'
            return False

        # Wait for a response
        try:
            m = await self.bot.wait_for('message', check=check, timeout=60.0)
        except AsyncTimeoutError as e:
            try:
                await ctx.send(self.bot.get_cog('ProposeRandomText').proposal_timed_out(instigator, target))
            except Exception as e:
                # If the bot was kicked, or access revoked, for example.
                pass
            self.bot.proposal_cache.remove(instigator.id)
            self.bot.proposal_cache.remove(target.id)
            return

        # Valid response recieved, see what their answer was
        response = check(m)
        if response == 'NO':
            await ctx.send(self.bot.get_cog('ProposeRandomText').declining_valid_proposal(instigator, target))
        elif response == 'YES':
            async with self.bot.database() as db:
                try:
                    await db.marry(instigator, target)
                except Exception as e:
                    return  # Only thrown if two people try to marry at once, so just return
            try:
                await ctx.send(self.bot.get_cog('ProposeRandomText').accepting_valid_proposal(instigator, target))
            except Exception as e:
                pass
            me = FamilyTreeMember.get(instigator.id)
            me._partner = target.id 
            them = FamilyTreeMember.get(target.id)
            them._partner = instigator.id

        self.bot.proposal_cache.remove(instigator.id)
        self.bot.proposal_cache.remove(target.id)


    @command()
    @cooldown(1, 5, BucketType.user)
    async def divorce(self, ctx:Context):
        '''
        Divorces you from your current spouse
        '''

        instigator = ctx.author

        # Get marriage data for the user
        instigator_data = FamilyTreeMember.get(instigator.id)

        # See why it could fail
        if instigator_data.partner == None:
            await ctx.send(self.bot.get_cog('DivorceRandomText').invalid_instigator(None, None))
            return
        target = ctx.guild.get_member(instigator_data.partner.id)
        if target == None:
            target_id = instigator_data.partner.id
        else:
            target_id = target.id


        if instigator_data.partner.id != target_id:
            await ctx.send(self.bot.get_cog('DivorceRandomText').invalid_target(None, None))
            return

        # At this point they can only be married
        async with self.bot.database() as db:
            await db('UPDATE marriages SET valid=FALSE where user_id=$1 OR user_id=$2', instigator.id, target_id)
        await ctx.send(self.bot.get_cog('DivorceRandomText').valid_target(instigator, target))

        me = instigator_data
        me._partner = None
        them = FamilyTreeMember.get(target_id)
        them._partner = None


def setup(bot:CustomBot):
    x = Marriage(bot)
    bot.add_cog(x)
