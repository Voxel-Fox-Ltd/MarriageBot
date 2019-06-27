from random import choice 

from cogs.utils.random_text.text_template import TextTemplate


class DivorceRandomText(TextTemplate):


    @classmethod
    def valid_target(cls, instigator=None, target=None):
        '''
        The given target and instigator are married
        '''

        return choice(cls.get_valid_strings([
            "Sorry, {target.mention}, looks like you're single now. Congrats, {instigator.mention}!",
            "I hope you figure it out some day, but for now it looks like the two of you are divorced, {instigator.mention}, {target.mention}.",
            "At least you don't have to deal with {instigator.mention} any more, {target.mention}, right...?",
            "Not the happiest of news for you, {target.mention}, but it looks like {instigator.mention} just left you...",
            "You and {target.mention} are now divorced. I wish you luck in your lives.",
            "You and your partner are now divorced. I wish you luck in your lives.",
            "I hope you figure it out some day, but for now, you and your partner are divorced, {instigator.mention}.",
        ], *['instigator' if instigator else None, 'target' if target else None])).format(instigator=instigator, target=target)

    
    @classmethod
    def instigator_is_unqualified(cls, instigator=None, target=None):
        '''
        The instigator isn't married at all
        '''

        return choice(cls.get_valid_strings([
            "Crazy idea, but you could try getting married first?",
            "It may seem like a stretch, but you need to marry someone before you can divorce them.",
            "Maybe try marrying them first?",
            "You're not married. Don't try to divorce strangers .-.",
        ], *['instigator' if instigator else None, 'target' if target else None])).format(instigator=instigator, target=target)
