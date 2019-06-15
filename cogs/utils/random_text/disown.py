from random import choice

from cogs.utils.random_text.text_template import TextTemplate


class DisownRandomText(TextTemplate):


    @staticmethod
    def valid_target(instigator=None, target=None):
        '''
        '''

        text = [
            "One child down, the rest to go.",
            "A sad day when a parent disowns their child...",
            "I'm sure this is very emotional for you. I'm sorry for your loss.",
        ]
        if target:
            text += [
                f"Oof, {target.mention}, {instigator.mention} doesn't seem to want you any more...",
                f"Well, {instigator.mention}, say goodbye to {target.mention}.",
                f"Might be good news for you, {target.mention}, but you're finally free of {instigator.mention}.",
            ]
        return choice(text)


    @staticmethod 
    def instigator_is_unqualified(instigator=None, target=None):
        '''
        '''

        return choice([
            "They aren't your child...",
            "Have you considered disowning someone who's *actually* your child?",
            "Strangely enough you can only disown *your* children.",
        ])
