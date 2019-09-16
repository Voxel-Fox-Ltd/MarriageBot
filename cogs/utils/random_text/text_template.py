import typing
import string
import random

import discord


class TextValidator(object):

    formatter = string.Formatter()

    @classmethod
    def get_string_kwargs(cls, string:str) -> typing.List[str]:
        """Returns a list of kwargs that the passed string contains"""

        return [i.split('.')[0] for _, i, _, _ in cls.formatter.parse(string) if i]

    @classmethod
    def get_valid_strings(cls, strings:typing.List[str], provided_arguments:typing.List[str]) -> typing.List[str]:
        """Filters down a list of inputs to outputs that are valid with the given locals,
        ie will filter out strings that require a 'target' if none has been provided"""

        v = []
        provided_arguments = set([i for i in provided_arguments if i])
        for i in strings:
            string_has = set(cls.get_string_kwargs(i))
            if provided_arguments == string_has or provided_arguments.issuperset(string_has):
                v.append(i)
        return v


def get_random_valid_string(func):
    def wrapper(*args):
        strings = func(*args)
        provided_arguments = [
            'instigator' if args[0] else None,
            'target' if args[1] else None
        ]
        valid_strings = TextValidator.get_valid_strings(strings, provided_arguments)
        return random.choice(valid_strings).format(instigator=args[0], target=args[1])
    return wrapper


class TextTemplate(object):

    def __init__(self, bot):
        self.bot = bot

    def process(self, instigator:discord.Member, target:discord.Member) -> str:
        """Processes a target/instigator pair to get the appropriate validation response"""

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
    def valid_target(instigator:discord.Member, target:discord.Member):
        """When the instigator picked a valid target for their action"""

        raise NotImplementedError()

    @staticmethod
    def target_is_family(instigator:discord.Member, target:discord.Member):
        """When the instigator and target are already related"""

        raise NotImplementedError()

    @staticmethod
    def target_is_me(instigator:discord.Member, target:discord.Member):
        """When the target is the bot"""

        raise NotImplementedError()

    @staticmethod
    def target_is_bot(instigator:discord.Member, target:discord.Member):
        """When the target is some other bot"""

        raise NotImplementedError()

    @staticmethod
    def target_is_you(instigator:discord.Member, target:discord.Member):
        """When the target and the instigator are the same person"""

        raise NotImplementedError()

    @staticmethod
    def instigator_is_instigator(instigator:discord.Member, target:discord.Member):
        """When the instigator has proposed to someone else already"""

        raise NotImplementedError()

    @staticmethod
    def instigator_is_target(instigator:discord.Member, target:discord.Member):
        """When the instigator is yet to respond to another proposal"""

        raise NotImplementedError()

    @staticmethod
    def target_is_instigator(instigator:discord.Member, target:discord.Member):
        """When the target has proposed to someone else"""

        raise NotImplementedError()

    @staticmethod
    def target_is_target(instigator:discord.Member, target:discord.Member):
        """When the target is already the target of someone else's proposal"""

        raise NotImplementedError()

    @staticmethod
    def request_timeout(instigator:discord.Member, target:discord.Member):
        """When a valid request times out"""

        raise NotImplementedError()

    @staticmethod
    def request_accepted(instigator:discord.Member, target:discord.Member):
        """When the target accepts the instigator's request"""

        raise NotImplementedError()

    @staticmethod
    def request_denied(instigator:discord.Member, target:discord.Member):
        """When the target says no to the instigator's request"""

        raise NotImplementedError()

    @staticmethod
    def target_is_unqualified(instigator:discord.Member, target:discord.Member):
        """The target is invalid for some other reason (eg they already have a parent etc)"""

        raise NotImplementedError()

    @staticmethod
    def instigator_is_unqualified(instigator:discord.Member, target:discord.Member):
        """The instigator is invalid for some other reason (eg they already have a parent etc)"""

        raise NotImplementedError()
