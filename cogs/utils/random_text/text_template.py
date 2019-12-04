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


def get_random_valid_string(func, instigator, target):
    """Wraps around a random_text output list and picks a random valid output based on the input args"""

    def wrapper():
        strings = func()
        provided_arguments = [
            'instigator' if instigator else None,
            'target' if target else None
        ]
        valid_strings = TextValidator.get_valid_strings(strings, provided_arguments)
        return random.choice(valid_strings).format(instigator=instigator, target=target)
    return wrapper


class TextTemplate(object):

    __slots__ = ("bot", "instigator", "target")

    def __init__(self, bot, instigator:discord.Member, target:discord.Member):
        self.bot = bot
        self.instigator = instigator
        self.target = target

    def process(self) -> str:
        """Processes a target/instigator pair to get the appropriate validation response"""

        instigator = self.instigator
        target = self.target

        # See if the instigator is in the proposal cache
        if self.bot.proposal_cache.get(instigator.id):
            x = self.bot.proposal_cache.get(instigator.id)
            if x[0] == 'INSTIGATOR':
                return get_random_valid_string(self.instigator_is_instigator, self.instigator, self.target)()
            elif x[0] == 'TARGET':
                return get_random_valid_string(self.instigator_is_target, self.instigator, self.target)()

        # Now check for the target
        if self.bot.proposal_cache.get(target.id):
            x = self.bot.proposal_cache.get(target.id)
            if x[0] == 'INSTIGATOR':
                return get_random_valid_string(self.target_is_instigator, self.instigator, self.target)()
            elif x[0] == 'TARGET':
                return get_random_valid_string(self.target_is_target, self.instigator, self.target)()

        # Check if they're proposing to the bot
        if target.id == self.bot.user.id:
            return get_random_valid_string(self.target_is_me, self.instigator, self.target)()

        # Check if they're proposing to themselves
        if instigator.id == target.id:
            return get_random_valid_string(self.target_is_you, self.instigator, self.target)()

        # Now check for any other bot
        if target.bot:
            return get_random_valid_string(self.target_is_bot, self.instigator, self.target)()

    @staticmethod
    def valid_target():
        """When the instigator picked a valid target for their action"""

        raise NotImplementedError()

    @staticmethod
    def target_is_family():
        """When the instigator and target are already related"""

        raise NotImplementedError()

    @staticmethod
    def target_is_me():
        """When the target is the bot"""

        raise NotImplementedError()

    @staticmethod
    def target_is_bot():
        """When the target is some other bot"""

        raise NotImplementedError()

    @staticmethod
    def target_is_you():
        """When the target and the instigator are the same person"""

        raise NotImplementedError()

    @staticmethod
    def instigator_is_instigator():
        """When the instigator has proposed to someone else already"""

        raise NotImplementedError()

    @staticmethod
    def instigator_is_target():
        """When the instigator is yet to respond to another proposal"""

        raise NotImplementedError()

    @staticmethod
    def target_is_instigator():
        """When the target has proposed to someone else"""

        raise NotImplementedError()

    @staticmethod
    def target_is_target():
        """When the target is already the target of someone else's proposal"""

        raise NotImplementedError()

    @staticmethod
    def request_timeout():
        """When a valid request times out"""

        raise NotImplementedError()

    @staticmethod
    def request_accepted():
        """When the target accepts the instigator's request"""

        raise NotImplementedError()

    @staticmethod
    def request_denied():
        """When the target says no to the instigator's request"""

        raise NotImplementedError()

    @staticmethod
    def target_is_unqualified():
        """The target is invalid for some other reason (eg they already have a parent etc)"""

        raise NotImplementedError()

    @staticmethod
    def instigator_is_unqualified():
        """The instigator is invalid for some other reason (eg they already have a parent etc)"""

        raise NotImplementedError()


def random_string_class_decorator(cls) -> TextTemplate:
    """Wraps around a random_text class and applies get_random_valid_string to all methods"""

    class Wrapper(object):

        def __init__(self, *args, **kwargs):
            self.other = cls(*args, **kwargs)

        def __getattribute__(self, attr):

            # Get current attrs
            try:
                return super().__getattribute__(attr)
            except AttributeError:
                pass

            # Get wrapped attrs
            method = self.other.__getattribute__(attr)
            if type(method) == type(self.__init__):
                return method
            return get_random_valid_string(method, self.other.instigator, self.other.target)

    return Wrapper
