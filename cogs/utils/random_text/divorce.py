from random import choice 

from cogs.utils.custom_bot import CustomBot


class DivorceRandomText(object):

    def __init__(self, bot:CustomBot):
        self.bot = bot 


    @staticmethod
    def valid_target(instigator, target):
        '''
        The given target and instigator are married
        '''

        if target:
            return choice([
                f"Sorry, {target.mention}, looks like you're single now. Congrats, {instigator.mention}!",
                f"I hope you figure it out some day, but for now it looks like the two of you are divorced, {instigator.mention}, {target.mention}.",
                f"At least you don't have to deal with {instigator.mention} any more, {target.mention}, right...?",
                f"Not the happiest of news for you, {target.mention}, but it looks like {instigator.mention} just left you...",
                f"You and {target.mention} are now divorced. I wish you luck in your lives.",
            ])
        return choice([
            "You and your partner are now divorced. I wish you luck in your lives.",
            f"I hope you figure it out some day, but for now, you and your partner are divorced, {instigator.mention}.",
        ])


    @staticmethod
    def invalid_target(instigator, target):
        '''
        The given target isn't married to the instigator
        '''

        return choice([
            "I don't think you can really divorce someone who isn't your spouse.",
            "You aren't married to them. Stop trying to split people up.",
            "It looks to me as if you're trying to divorce someone you aren't with.",
        ])

    
    @staticmethod
    def invalid_instigator(instigator, target):
        '''
        The instigator isn't married at all
        '''

        return choice([
            "Crazy idea, but you could try getting married first?",
            "It may seem like a stretch, but you need to marry someone before you can divorce them.",
            "Maybe try marrying them first?",
            "You're not married. Don't try to divorce strangers .-.",
        ])


def setup(bot:CustomBot):
    x = DivorceRandomText(bot)
    bot.add_cog(x)
