from random import choice

from cogs.utils.custom_bot import CustomBot


class EmancipateRandomText(object):

    def __init__(self, bot:CustomBot):
        self.bot = bot


    @staticmethod
    def valid_target(instigator, target):
        '''
        '''

        if target:
            return choice([
                f"Looks like {target.mention} left you, {instigator.mention}. I'm sorry for your loss."
                f"You're free of {target.mention}, {instigator.mention}!"
                f"Say goodbye to {target.mention}, {instigator.mention}! You're parentless now!"
            ])
        return choice([
            f"Freedom for you, {instigator.mention}!",
            "Have fun living in the streets!",
            "You no longer have a parent.\n... Don't think too hard about it."
        ])


    @staticmethod
    def invalid_target(instigator, target):
        '''
        '''

        return choice([
        ])


def setup(bot:CustomBot):
    x = EmancipateRandomText(bot)
    bot.add_cog(x)
