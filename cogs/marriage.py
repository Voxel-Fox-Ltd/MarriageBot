from re import compile
from asyncio import TimeoutError as AsyncTimeoutError, wait_for

from discord import Member
from discord.ext.commands import command, Context, cooldown
from discord.ext.commands import MissingRequiredArgument, CommandOnCooldown, BadArgument
from discord.ext.commands.cooldowns import BucketType

from cogs.utils.custom_bot import CustomBot
from cogs.utils.family_tree.family_tree_member import FamilyTreeMember
from cogs.utils.checks.user_block import BlockedUserError, UnblockedMember
from cogs.utils.acceptance_check import AcceptanceCheck
from cogs.utils.custom_cog import Cog

from cogs.utils.random_text.text_template import TextTemplate
from cogs.utils.random_text.propose import ProposeRandomText
from cogs.utils.random_text.divorce import DivorceRandomText


class Marriage(Cog):
    '''
    The marriage cog
    Handles all marriage/divorce/etc commands
    '''

    def __init__(self, bot:CustomBot):
        super().__init__(self.__class__.__name__)
        self.bot = bot


    async def cog_command_error(self, ctx:Context, error):
        '''
        Local error handler for the cog
        '''

        # Throw errors properly for me
        if ctx.author.id in self.bot.config['owners'] and not isinstance(error, CommandOnCooldown):
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

        # Blocked user
        elif isinstance(error, BlockedUserError):
            await ctx.send("That user has blocked you, so you can't run this command.")
            return
    
        # Argument conversion error
        elif isinstance(error, BadArgument):
            argument_text = self.bot.bad_argument.search(str(error)).group(2)
            await ctx.send(f"User `{argument_text}` could not be found.")
            return


    @command(aliases=['marry'])
    @cooldown(1, 5, BucketType.user)
    async def propose(self, ctx:Context, *, target:UnblockedMember):
        '''
        Lets you propose to another Discord user
        '''

        # Variables we're gonna need for later
        instigator = ctx.author
        instigator_tree = FamilyTreeMember.get(instigator.id, self.bot.get_tree_guild_id(ctx.guild.id))
        target_tree = FamilyTreeMember.get(target.id, self.bot.get_tree_guild_id(ctx.guild.id))

        # Manage output strings
        text_processor = ProposeRandomText(self.bot)
        text = text_processor.process(instigator, target)
        if text:
            await ctx.send(text) 
            return

        # See if our user is already married
        if instigator_tree._partner:
            await ctx.send(text_processor.instigator_is_unqualified(instigator, target))
            return

        # See if the *target* is already married 
        if target_tree._partner:
            await ctx.send(text_processor.target_is_unqualified(instigator, target))
            return

        # See if they're already related
        if instigator_tree.get_relation(target_tree):
            await ctx.send(text_processor.target_is_family(instigator, target))
            return

        # Neither are married, set up the proposal
        await ctx.send(text_processor.valid_target(instigator, target))
        self.bot.proposal_cache.add(instigator, target, 'MARRIAGE')

        # Wait for a response
        try:
            check = AcceptanceCheck(target.id, ctx.channel.id).check
            m = await self.bot.wait_for('message', check=check, timeout=60.0)
        except AsyncTimeoutError as e:
            await ctx.send(text_processor.request_timeout(instigator, target), ignore_error=True)
            self.bot.proposal_cache.remove(instigator, target)
            return

        # Valid response recieved, see what their answer was
        response = check(m)

        # They said no
        if response == 'NO':
            await ctx.send(text_processor.declining_valid_proposal(instigator, target), ignore_error=True)
            self.bot.proposal_cache.remove(instigator, target)
            return

        # They said yes!
        async with self.bot.database() as db:
            try:
                await db.marry(instigator, target, self.bot.get_tree_guild_id(ctx.guild.id))
            except Exception as e:
                return 
        await ctx.send(text_processor.request_accepted(instigator, target), ignore_error=True)

        # Cache values locally
        instigator_tree._partner = target.id 
        target_tree._partner = instigator.id

        # Ping em off over redis
        async with self.bot.redis() as re:
            await re.publish_json('TreeMemberUpdate', instigator_tree.to_json())
            await re.publish_json('TreeMemberUpdate', target_tree.to_json())

        # Remove users from proposal cache
        self.bot.proposal_cache.remove(instigator, target)


    @command()
    @cooldown(1, 5, BucketType.user)
    async def divorce(self, ctx:Context):
        '''
        Divorces you from your current spouse
        '''

        # Variables we're gonna need for later
        instigator = ctx.author
        instigator_tree = FamilyTreeMember.get(instigator.id, self.bot.get_tree_guild_id(ctx.guild.id))

        # Manage output strings
        text_processor = DivorceRandomText(self.bot)

        # See if they have a partner to divorce
        if instigator_tree._partner == None:
            await ctx.send(text_processor.instigator_is_unqualified())
            return

        # They have a partner - fetch their data
        target = await self.bot.fetch_user(instigator_tree._partner)
        target_tree = instigator_tree.partner

        # Remove them from the database
        async with self.bot.database() as db:
            await db(
                'DELETE FROM marriages WHERE (user_id=$1 OR user_id=$2) AND guild_id=$3', 
                instigator.id, 
                target_tree.id, 
                self.bot.get_tree_guild_id(ctx.guild.id)
            )
        await ctx.send(text_processor.valid_target(instigator, target))

        # Remove from cache
        instigator_tree._partner = None
        target_tree._partner = None

        # Ping over redis
        async with self.bot.redis() as re:
            await re.publish_json('TreeMemberUpdate', instigator_tree.to_json())
            await re.publish_json('TreeMemberUpdate', target_tree.to_json())


def setup(bot:CustomBot):
    x = Marriage(bot)
    bot.add_cog(x)
