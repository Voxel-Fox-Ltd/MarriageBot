from random import choice

from discord.ext.commands import Cog

from cogs.utils.custom_bot import CustomBot


class EmancipateRandomText(Cog):

    def __init__(self, bot:CustomBot):
        self.bot = bot


    @staticmethod
    def valid_target(instigator, target):
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
    def invalid_target(instigator, target):
        '''
        '''

        return choice([
            "You don't actually have a parent. This is awkward.",
            "You're already an orphan though!",
        ])


def setup(bot:CustomBot):
    x = EmancipateRandomText(bot)
    bot.add_cog(x)
