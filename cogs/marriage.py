from re import compile
from asyncio import TimeoutError

from discord import Member
from discord.ext.commands import command, Context, cooldown
from discord.ext.commands.cooldowns import BucketType

from cogs.utils.custom_bot import CustomBot
from cogs.utils.family_tree.family_tree_member import FamilyTreeMember



class Marriage(object):
    '''
    The marriage cog
    Handles all marriage/divorce/etc commands
    '''

    def __init__(self, bot:CustomBot):
        self.bot = bot

        # Proposal text
        self.proposal_yes = compile(r"(i do)|(yes)|(of course)|(definitely)|(absolutely)|(yeah)|(yea)|(sure)|(m!accept)")
        self.proposal_no = compile(r"(i don't)|(i dont)|(no)|(to think)|(i'm sorry)|(im sorry)")

        # Get random text for this cog
        self.marriage_random_text = None
        self.divorce_random_text = None
        self.bot.loop.create_task(self.get_marriage_random_text())
        self.bot.loop.create_task(self.get_divorce_random_text())

    
    async def get_marriage_random_text(self):
        await self.bot.wait_until_ready()
        self.marriage_random_text = self.bot.cogs.get('ProposeRandomText')

    
    async def get_divorce_random_text(self):
        await self.bot.wait_until_ready()
        self.divorce_random_text = self.bot.cogs.get('DivorceRandomText')


    def __local_check(self, ctx:Context):
        return self.marriage_random_text != None and self.divorce_random_text != None


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
                await ctx.send(self.marriage_random_text.proposing_while_instigator(instigator, target))
            elif x[0] == 'TARGET':
                await ctx.send(self.marriage_random_text.proposing_while_target(instigator, target))
            return
        elif target.id in self.bot.proposal_cache:
            x = self.bot.proposal_cache.get(target.id)
            if x[0] == 'INSTIGATOR':
                await ctx.send(self.marriage_random_text.proposing_to_instigator(instigator, target))
            elif x[0] == 'TARGET':
                await ctx.send(self.marriage_random_text.proposing_to_target(instigator, target))
            return

        # Manage exclusions
        if target.id == self.bot.user.id:
            await ctx.send(self.marriage_random_text.proposing_to_me(instigator, target))
            return
        elif target.bot or instigator.bot:
            await ctx.send(self.marriage_random_text.proposing_to_bot(instigator, target))
            return
        elif instigator.id == target.id:
            await ctx.send(self.marriage_random_text.proposing_to_themselves(instigator, target))
            return

        # See if they're married or in the family already
        await ctx.trigger_typing()
        user_tree = FamilyTreeMember.get(instigator.id)
        root = user_tree.get_root()
        tree_id_list = [i.id for i in root.span(add_parent=True, expand_upwards=True)]

        if target.id in tree_id_list:
            await ctx.send(self.marriage_random_text.proposing_to_family(instigator, target))
            return
        if user_tree.partner:
            await ctx.send(self.marriage_random_text.proposing_when_married(instigator, target))
            return
        elif FamilyTreeMember.get(target.id).partner:
            await ctx.send(self.marriage_random_text.proposing_to_married(instigator, target))
            return

        # Neither are married, set up the proposal
        await ctx.send(self.marriage_random_text.valid_proposal(instigator, target))
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
        except TimeoutError as e:
            try:
                await ctx.send(self.marriage_random_text.proposal_timed_out(instigator, target))
            except Exception as e:
                # If the bot was kicked, or access revoked, for example.
                pass
            self.bot.proposal_cache.remove(instigator.id)
            self.bot.proposal_cache.remove(target.id)
            return

        # Valid response recieved, see what their answer was
        response = check(m)
        if response == 'NO':
            await ctx.send(self.marriage_random_text.declining_valid_proposal(instigator, target))
        elif response == 'YES':
            async with self.bot.database() as db:
                try:
                    await db.marry(instigator, target)
                except Exception as e:
                    return  # Only thrown if two people try to marry at once, so just return
            try:
                await ctx.send(self.marriage_random_text.accepting_valid_proposal(instigator, target))
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
            await ctx.send(self.divorce_random_text.invalid_instigator(None, None))
            return
        target = ctx.guild.get_member(instigator_data.partner.id)
        if target == None:
            target_id = instigator_data.partner.id
        else:
            target_id = target.id


        if instigator_data.partner.id != target_id:
            await ctx.send(self.divorce_random_text.invalid_target(None, None))
            return

        # At this point they can only be married
        async with self.bot.database() as db:
            await db('UPDATE marriages SET valid=FALSE where user_id=$1 OR user_id=$2', instigator.id, target_id)
        await ctx.send(self.divorce_random_text.valid_target(instigator, target))

        me = instigator_data
        me._partner = None
        them = FamilyTreeMember.get(target_id)
        them._partner = None


def setup(bot:CustomBot):
    x = Marriage(bot)
    bot.add_cog(x)
