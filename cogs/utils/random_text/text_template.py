import typing
import string
import random
import collections
import functools

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
    """Wraps around a random_text output list and picks a random valid output based on the input args"""

    instigator = func.__self__.instigator
    target = func.__self__.target

    @functools.wraps(func)
    def wrapper():
        strings = func()
        provided_arguments = [
            'instigator' if instigator else None,
            'target' if target else None
        ]
        valid_strings = TextValidator.get_valid_strings(strings, provided_arguments)
        return random.choice(valid_strings).format(instigator=instigator, target=target)
    return wrapper


def random_string_class_decorator(cls) -> 'TextTemplate':
    """Wraps around a random_text class and applies get_random_valid_string to all methods"""

    @functools.wraps(cls)
    class Wrapper(object):

        original = cls

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
            if attr in self.other.WANTS_RANDOM_STRINGS:
                return get_random_valid_string(method)
            return method

    return Wrapper


@random_string_class_decorator
class TextTemplate(object):

    all_random_text = collections.defaultdict(lambda: collections.defaultdict(list))
    bot = None
    WANTS_RANDOM_STRINGS = [
        'valid_target', 'target_is_family', 'target_is_me', 'target_is_bot', 'target_is_you',
        'instigator_is_instigator', 'instigator_is_target', 'target_is_instigator',
        'target_is_target', 'request_timeout', 'request_accepted', 'request_denied',
        'target_is_unqualified', 'instigator_is_unqualified',
    ]

    __slots__ = ("instigator", "target", "responses")

    def __init__(self, command:str, instigator:discord.Member, target:discord.Member):
        self.instigator = instigator
        self.target = target
        self.responses = self.all_random_text.get(command)

    def process(self) -> str:
        """Processes a target/instigator pair to get the appropriate validation response"""

        instigator = self.instigator
        target = self.target

        # See if the instigator is in the proposal cache
        if self.bot.proposal_cache.get(instigator.id):
            x = self.bot.proposal_cache.get(instigator.id)
            if x[0] == 'INSTIGATOR':
                return get_random_valid_string(self.instigator_is_instigator)()
            elif x[0] == 'TARGET':
                return get_random_valid_string(self.instigator_is_target)()

        # Now check for the target
        if self.bot.proposal_cache.get(target.id):
            x = self.bot.proposal_cache.get(target.id)
            if x[0] == 'INSTIGATOR':
                return get_random_valid_string(self.target_is_instigator)()
            elif x[0] == 'TARGET':
                return get_random_valid_string(self.target_is_target)()

        # Check if they're proposing to the bot
        if target.id == self.bot.user.id:
            return get_random_valid_string(self.target_is_me)()

        # Check if they're proposing to themselves
        if instigator.id == target.id:
            return get_random_valid_string(self.target_is_you)()

        # Now check for any other bot
        if target.bot:
            return get_random_valid_string(self.target_is_bot)()

    def valid_target(self):
        """When the instigator picked a valid target for their action"""

        return self.responses.get('valid_target', list())

    def target_is_family(self):
        """When the instigator and target are already related"""

        return self.responses.get('target_is_family', list())

    def target_is_me(self):
        """When the target is the bot"""

        return self.responses.get('target_is_me', list())

    def target_is_bot(self):
        """When the target is some other bot"""

        return self.responses.get('target_is_bot', list())

    def target_is_you(self):
        """When the target and the instigator are the same person"""

        return self.responses.get('target_is_you', list())

    def instigator_is_instigator(self):
        """When the instigator has proposed to someone else already"""

        return self.responses.get('instigator_is_instigator', list())

    def instigator_is_target(self):
        """When the instigator is yet to respond to another proposal"""

        return self.responses.get('instigator_is_target', list())

    def target_is_instigator(self):
        """When the target has proposed to someone else"""

        return self.responses.get('target_is_instigator', list())

    def target_is_target(self):
        """When the target is already the target of someone else's proposal"""

        return self.responses.get('target_is_target', list())

    def request_timeout(self):
        """When a valid request times out"""

        return self.responses.get('request_timeout', list())

    def request_accepted(self):
        """When the target accepts the instigator's request"""

        return self.responses.get('request_accepted', list())

    def request_denied(self):
        """When the target says no to the instigator's request"""

        return self.responses.get('request_denied', list())

    def target_is_unqualified(self):
        """The target is invalid for some other reason (eg they already have a parent etc)"""

        return self.responses.get('target_is_unqualified', list())

    def instigator_is_unqualified(self):
        """The instigator is invalid for some other reason (eg they already have a parent etc)"""

        return self.responses.get('instigator_is_unqualified', list())
