from random import choice

from cogs.utils.random_text.text_template import TextTemplate


class EmancipateRandomText(TextTemplate):


    @classmethod
    def valid_target(cls, instigator=None, target=None):
        '''
        '''

        return choice(cls.get_valid_strings([
            "Looks like {instigator.mention} left you, {target.mention}. I'm sorry for your loss.",
            "You're free of {target.mention}, {instigator.mention}!",
            "Say goodbye to {target.mention}, {instigator.mention}! You're parentless now!",
            "Freedom for you, {instigator.mention}!",
            "Have fun living in the streets!",
            "You no longer have a parent.\n... Don't think too hard about it.",
        ], *['instigator' if instigator else None, 'target' if target else None])).format(instigator=instigator, target=target)


    @classmethod
    def instigator_is_unqualified(cls, instigator=None, target=None):
        '''
        '''

        return choice(cls.get_valid_strings([
            "You don't actually have a parent. This is awkward.",
            "You're already an orphan though!",
        ], *['instigator' if instigator else None, 'target' if target else None])).format(instigator=instigator, target=target)
