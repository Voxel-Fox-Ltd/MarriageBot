from random import choice

from cogs.utils.random_text.text_template import TextTemplate


class EmancipateRandomText(TextTemplate):


    @staticmethod
    def valid_target(instigator=None, target=None):
        '''
        '''

        if target:
            return choice([
                f"Looks like {instigator.mention} left you, {target.mention}. I'm sorry for your loss.",
                f"You're free of {target.mention}, {instigator.mention}!",
                f"Say goodbye to {target.mention}, {instigator.mention}! You're parentless now!",
            ])
        return choice([
            f"Freedom for you, {instigator.mention}!",
            "Have fun living in the streets!",
            "You no longer have a parent.\n... Don't think too hard about it.",
        ])


    @staticmethod
    def instigator_is_unqualified(instigator=None, target=None):
        '''
        '''

        return choice([
            "You don't actually have a parent. This is awkward.",
            "You're already an orphan though!",
        ])
