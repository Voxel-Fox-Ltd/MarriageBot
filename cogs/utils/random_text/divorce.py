from random import choice 

from cogs.utils.random_text.text_template import TextTemplate


class DivorceRandomText(TextTemplate):


    @staticmethod
    def valid_target(instigator=None, target=None):
        '''
        The given target and instigator are married
        '''

        strings = []
        if target:
            strings.extend([
                f"Sorry, {target.mention}, looks like you're single now. Congrats, {instigator.mention}!",
                f"I hope you figure it out some day, but for now it looks like the two of you are divorced, {instigator.mention}, {target.mention}.",
                f"At least you don't have to deal with {instigator.mention} any more, {target.mention}, right...?",
                f"Not the happiest of news for you, {target.mention}, but it looks like {instigator.mention} just left you...",
                f"You and {target.mention} are now divorced. I wish you luck in your lives.",
            ])
        strings.extend([
            "You and your partner are now divorced. I wish you luck in your lives.",
            f"I hope you figure it out some day, but for now, you and your partner are divorced, {instigator.mention}.",
        ])
        return choice(strings)

    
    @staticmethod
    def instigator_is_unqualified(instigator=None, target=None):
        '''
        The instigator isn't married at all
        '''

        return choice([
            "Crazy idea, but you could try getting married first?",
            "It may seem like a stretch, but you need to marry someone before you can divorce them.",
            "Maybe try marrying them first?",
            "You're not married. Don't try to divorce strangers .-.",
        ])
