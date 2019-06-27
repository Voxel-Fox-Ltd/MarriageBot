from typing import List
from string import Formatter

from discord import Member


class TextTemplate(object):

    formatter = Formatter()


    def __init__(self, bot):
        self.bot = bot 


    @classmethod 
    def get_string_kwargs(cls, string:str) -> List[str]:
        '''Returns a list of kwargs that the passed string contains'''

        return [i.split('.')[0] for _, i, _, _ in cls.formatter.parse(string) if i]

    
    @classmethod 
    def get_valid_strings(cls, strings:str, *provided) -> List[str]:
        '''Filters down a list of inputs to outputs that are valid with the given locals,
        ie will filter out strings that require a 'target' if none has been provided'''

        v = []
        provided = set([i for i in provided if i])
        for i in strings:
            string_has = set(cls.get_string_kwargs(i))
            if provided == string_has or provided.issuperset(string_has):
                v.append(i) 
        return v


    def process(self, instigator:Member, target:Member) -> str:
        '''
        Processes a target/instigator pair to get the appropriate validation response
        '''
        
        # See if the instigator is in the proposal cache
        if self.bot.proposal_cache.get(instigator.id):
            x = self.bot.proposal_cache.get(instigator.id)
            if x[0] == 'INSTIGATOR': 
                return self.instigator_is_instigator(instigator, target)
            elif x[0] == 'TARGET': 
                return self.instigator_is_target(instigator, target)

        # Now check for the target
        if self.bot.proposal_cache.get(target.id):
            x = self.bot.proposal_cache.get(target.id)
            if x[0] == 'INSTIGATOR': 
                return self.target_is_instigator(instigator, target)
            elif x[0] == 'TARGET': 
                return self.target_is_target(instigator, target)

        # Check if they're proposing to the bot
        if target.id == self.bot.user.id:
            return self.target_is_me(instigator, target)

        # Check if they're proposing to themselves
        if instigator.id == target.id:
            return self.target_is_you(instigator, target)

        # Now check for any other bot
        if target.bot:
            return self.target_is_bot(instigator, target)

    @staticmethod
    def valid_target(instigator:Member, target:Member):
        raise NotImplementedError()

    @staticmethod
    def target_is_family(instigator:Member, target:Member):
        raise NotImplementedError()

    @staticmethod
    def target_is_me(instigator:Member, target:Member):
        raise NotImplementedError()

    @staticmethod
    def target_is_bot(instigator:Member, target:Member):
        raise NotImplementedError()

    @staticmethod
    def target_is_you(instigator:Member, target:Member):
        raise NotImplementedError()

    @staticmethod
    def instigator_is_instigator(instigator:Member, target:Member):
        raise NotImplementedError()

    @staticmethod
    def instigator_is_target(instigator:Member, target:Member):
        raise NotImplementedError()

    @staticmethod
    def target_is_instigator(instigator:Member, target:Member):
        raise NotImplementedError()

    @staticmethod
    def target_is_target(instigator:Member, target:Member):
        raise NotImplementedError()

    @staticmethod
    def request_timeout(instigator:Member, target:Member):
        raise NotImplementedError()

    @staticmethod
    def request_accepted(instigator:Member, target:Member):
        raise NotImplementedError()

    @staticmethod
    def request_denied(instigator:Member, target:Member):
        raise NotImplementedError()

    @staticmethod
    def target_is_unqualified(instigator:Member, target:Member):
        raise NotImplementedError()

    @staticmethod
    def instigator_is_unqualified(instigator:Member, target:Member):
        raise NotImplementedError()
