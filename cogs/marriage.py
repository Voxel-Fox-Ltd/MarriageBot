from re import compile
from asyncio import TimeoutError
from discord import Member
from discord.ext.commands import command, Context
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
        self._random_text = None


    @property
    def random_text(self):
        if not self._random_text:
            self._random_text = self.bot.cogs['MarriageRandomText']
        return self._random_text


    @command(aliases=['marry'])
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
                await ctx.send(self.random_text.proposing_while_instigator(instigator, target))
            elif x[0] == 'TARGET':
                await ctx.send(self.random_text.proposing_while_target(instigator, target))
            return
        elif target.id in self.bot.proposal_cache:
            x = self.bot.proposal_cache.get(target.id)
            if x[0] == 'INSTIGATOR':
                await ctx.send(self.random_text.proposing_to_instigator(instigator, target))
            elif x[0] == 'TARGET':
                await ctx.send(self.random_text.proposing_to_target(instigator, target))
            return

        # Manage exclusions
        if target.id == self.bot.user.id:
            await ctx.send(self.random_text.proposing_to_me(instigator, target))
            return
        elif target.bot or instigator.bot:
            await ctx.send(self.random_text.proposing_to_bot(instigator, target))
            return
        elif instigator.id == target.id:
            await ctx.send(self.random_text.proposing_to_themselves(instigator, target))
            return

        # See if they're married or in the family already
        await ctx.trigger_typing()
        user_tree = FamilyTreeMember.get(instigator.id)
        root = user_tree.expand_backwards(-1)
        tree_id_list = [i.id for i in root.span(add_parent=True, expand_upwards=True)]

        if target.id in tree_id_list:
            await ctx.send(self.random_text.proposing_to_family(instigator, target))
            return
        if user_tree.partner:
            await ctx.send(self.random_text.proposing_when_married(instigator, target))
            return
        elif FamilyTreeMember.get(target.id).partner:
            await ctx.send(self.random_text.proposing_to_married(instigator, target))
            return

        # Neither are married, set up the proposal
        await ctx.send(self.random_text.valid_proposal(instigator, target))
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
                await ctx.send(self.random_text.proposal_timed_out(instigator, target))
            except Exception as e:
                # If the bot was kicked, or access revoked, for example.
                pass
            self.bot.proposal_cache.remove(instigator.id)
            self.bot.proposal_cache.remove(target.id)
            return

        # Valid response recieved, see what their answer was
        response = check(m)
        if response == 'NO':
            await ctx.send(self.random_text.declining_valid_proposal(instigator, target))
        elif response == 'YES':
            async with self.bot.database() as db:
                try:
                    await db.marry(instigator, target)
                except Exception as e:
                    return  # Only thrown if two people try to marry at once, so just return
            try:
                await ctx.send(self.random_text.accepting_valid_proposal(instigator, target))
            except Exception as e:
                pass
            me = FamilyTreeMember.get(instigator.id)
            me.partner = target.id 
            them = FamilyTreeMember.get(target.id)
            them.partner = instigator.id

        self.bot.proposal_cache.remove(instigator.id)
        self.bot.proposal_cache.remove(target.id)


    @command()
    async def divorce(self, ctx:Context, user:Member=None):
        '''
        Divorces you from your current spouse
        '''

        instigator = ctx.author
        target = user  # Just so "target" didn't show up in the help message

        # Get marriage data for the user
        instigator_data = FamilyTreeMember.get(instigator.id)

        # See why it could fail
        if instigator_data.partner == None:
            await ctx.send("You're not married. Don't try to divorce strangers .-.")
            return
        elif target == None:
            target = ctx.guild.get_member(instigator_data.partner)
            if target == None:
                target_id = instigator_data.partner 
            else:
                target_id = target.id
        else:
            target_id = target.id


        if instigator_data.partner != target_id:
            await ctx.send("You aren't married to that person .-.")
            return

        # At this point they can only be married
        async with self.bot.database() as db:
            await db('UPDATE marriages SET valid=FALSE where user_id=$1 OR user_id=$2', instigator.id, target_id)
        if target:            
            await ctx.send(f"You and {target.mention} are now divorced. I wish you luck in your lives.")
        else:
            await ctx.send(f"You and your partner are now divorced. I wish you luck in your lives.")

        me = instigator_data
        me.partner = None
        them = FamilyTreeMember.get(target_id)
        them.partner = None


def setup(bot:CustomBot):
    x = Marriage(bot)
    bot.add_cog(x)
