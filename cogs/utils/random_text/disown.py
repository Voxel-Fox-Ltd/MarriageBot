from random import choice

from cogs.utils.random_text.text_template import TextTemplate


class DisownRandomText(TextTemplate):


    @classmethod
    def valid_target(cls, instigator=None, target=None):
        '''
        '''

        return choice(cls.get_valid_strings([
            "One child down, the rest to go.",
            "A sad day when a parent disowns their child...",
            "I'm sure this is very emotional for you. I'm sorry for your loss.",
            "Oof, {target.mention}, {instigator.mention} doesn't seem to want you any more...",
            "Well, {instigator.mention}, say goodbye to {target.mention}.",
            "Might be good news for you, {target.mention}, but you're finally free of {instigator.mention}.",
        ], *['instigator' if instigator else None, 'target' if target else None])).format(instigator=instigator, target=target)


    @classmethod 
    def instigator_is_unqualified(cls, instigator=None, target=None):
        '''
        '''

        return choice(cls.get_valid_strings([
            "They aren't your child...",
            "Have you considered disowning someone who's *actually* your child?",
            "Strangely enough you can only disown *your* children.",
        ], *['instigator' if instigator else None, 'target' if target else None])).format(instigator=instigator, target=target)
