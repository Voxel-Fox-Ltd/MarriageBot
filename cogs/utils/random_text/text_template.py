from discord import Member

from discord.ext.commands import Cog

from cogs.utils.custom_bot import CustomBot


class TextTemplate(Cog):
    
    def __init__(self, bot:CustomBot):
        self.bot = bot

    def process(self, cog, instigator:Member, target:Member) -> str:
        '''
        Processes a target/instigator pair to get the appropriate validation response
        '''

        # Get the right cog
        if not isinstance(cog, Cog):
            cog = self.bot.get_cog(cog)
        
        # See if the instigator is in the proposal cache
        if instigator.id in self.bot.proposal_cache:
            x = self.bot.proposal_cache.get(instigator.id)
            if x[0] == 'INSTIGATOR': 
                return cog.instigator_is_instigator(instigator, target)
            elif x[0] == 'TARGET': 
                return cog.instigator_is_target(instigator, target)

        # Now check for the target
        elif target.id in self.bot.proposal_cache:
            x = self.bot.proposal_cache.get(target.id)
            if x[0] == 'INSTIGATOR': 
                return cog.target_is_instigator(instigator, target)
            elif x[0] == 'TARGET': 
                return cog.target_is_target(instigator, target)

        # Check if they're proposing to the bot
        if target.id == self.bot.user.id:
            return cog.target_is_me(instigator, target)

        # Check if they're proposing to themselves
        elif instigator.id == target.id:
            return cog.target_is_you(instigator, target)

        # Now check for any other bot
        elif target.bot:
            return cog.target_id_bot(instigator, target)

    @staticmethod
    def valid_target(instigator:Member, target:Member):
        ...

    @staticmethod
    def target_is_family(instigator:Member, target:Member):
        ...

    @staticmethod
    def target_is_me(instigator:Member, target:Member):
        ...

    @staticmethod
    def target_is_bot(instigator:Member, target:Member):
        ...

    @staticmethod
    def target_is_you(instigator:Member, target:Member):
        ...

    @staticmethod
    def instigator_is_instigator(instigator:Member, target:Member):
        ...

    @staticmethod
    def instigator_is_target(instigator:Member, target:Member):
        ...

    @staticmethod
    def target_is_instigator(instigator:Member, target:Member):
        ...

    @staticmethod
    def target_is_target(instigator:Member, target:Member):
        ...

    @staticmethod
    def request_timeout(instigator:Member, target:Member):
        ...

    @staticmethod
    def request_accepted(instigator:Member, target:Member):
        ...

    @staticmethod
    def request_denied(instigator:Member, target:Member):
        ...

    @staticmethod
    def target_is_unqualified(instigator:Member, target:Member):
        ...


def setup(bot:CustomBot):
    x = TextTemplate(bot)
    bot.add_cog(x)
