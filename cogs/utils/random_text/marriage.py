from random import choice
from cogs.utils.custom_bot import CustomBot


class MarriageRandomText(object):


    def __init__(self, bot:CustomBot):
        self.bot = bot


    @staticmethod
    def valid_proposal(instigator, target):
        '''
        When you make a valid proposal
        '''

        return choice([
            f"{target.mention}, do you accept {instigator.mention}'s proposal?",
            f"{target.mention}, {instigator.mention} has proposed to you. What do you say?",
            f"{instigator.mention} may be young, but they're full of heart. Do you want to marry them, {target.mention}?",
            f"{instigator.mention} finally wants to settle down with you, {target.mention}. Do you accept?",
            f"{target.mention}, will you marry {instigator.mention}?",
            f"{instigator.mention} wants you to be the love of their life, {target.mention}. Do you accept?",
        ])


    @staticmethod
    def proposing_to_married(instigator, target):
        '''
        When you're proposing to a married person
        '''

        return choice([
            f"I hate to tell you this, {instigator.mention}, but they're already married...",
            f"I don't know if you knew this but they're already married, {instigator.mention}...",
            f"Oh, uh, sorry {instigator.mention}, but they're already seeing someone.",
            f"Ah... this is awkward... they already have someone, {instigator.mention}...",
            f"Polygamy is much harder to store in a database, {instigator.mention}. My apologies.",
        ])


    @staticmethod
    def proposing_when_married(instigator, target):
        '''
        When you make a proposal while married
        '''

        return choice([
            f"Maybe you should wait until after you're divorced, {instigator.mention}.",
            f"You already have someone, {instigator.mention}."
            f"You're not single, {instigator.mention}.",
            f"I hate to rain on your parade, {instigator.mention}, but I don't think that appropriate while you're married already.",
            f"Polygamy is much harder to store in a database, {instigator.mention}. My apologies.",
            f"Unfortunately I can't show family trees with polygamy in them, {instigator.mention}.",
        ])


    @staticmethod
    def proposing_to_family(instigator, target):
        '''
        When you propose to a family member
        '''

        return choice([
            f"That... that's a family member of yours, {instigator.mention}...",
            f"Though we support free speech and all, you can't really marry someone you're related to, {instigator.mention}.",
            f"We've made great strides towards equality recently, {instigator.mention}, but you still can't marry a relative of yours.",
            f"{instigator.mention} you're related to them .-.",
            f"Incestuous relationships tend to mess up the family tree, so I'm afraid I'll have to say no, {instigator.mention}.",
        ])


    @staticmethod
    def proposing_while_instigator(instigator, target):
        '''
        When you propose while you're already waiting on a response from another proposal
        '''

        return choice([
            f"You've already proposed to someone, {instigator.mention}, just wait for a response.",
            f"You can only make one proposal at a time, {instigator.mention}.",
            f"One proposal at a time is the max limit, {instigator.mention}.",
            f"Calm it, {instigator.mention}, you already proposed to someone!",
        ])


    @staticmethod
    def proposing_while_target(instigator, target):
        '''
        When you propose while they're yet to respond to another proposal
        '''

        return choice([
            "Sorry but you've gotta answer your current proposal before you can make one of your own.",
            "You need to answer the proposal you have already before you can make a new one.",
            f"You've been proposed to already, {instigator.mention}. Please respond before moving on.",
            "Don't you want to answer the proposal you have already?",
            f"Someone already proposed to you though! Answer them first, {instigator.mention}.",
        ])


    @staticmethod
    def proposing_to_instigator(instigator, target):
        '''
        When they propose to someone who's already proposed to someone
        '''

        return choice([
            "I'm afraid they've already proposed to someone. Give it a minute - see how it goes.",
            "They seem to have just proposed to someone. See how that goes before you try yourself.",
            "Hold your horses - they've just proposed to someone else.",
            "They're waiting on a response from soneone else; give it a minute.",
            "I think they're interested in someone else, having just proposed to them.",
        ])


    @staticmethod
    def proposing_to_target(instigator, target):
        '''
        When they propose to someone who's yet to respond to another
        '''

        return choice([
            "They're a popular choice, I see. Wait to see what they say to the other proposal they have before trying yourself.",
            "Someone just proposed to them. See what they say there first.",
            "Woah, hold on a minute - someone else proposed first. I wonder what they'll say...",
        ])


    @staticmethod
    def proposing_to_me(instigator, target):
        '''
        When they propose to the bot
        '''

        return choice([
            "I'm flattered, but my heart belongs to another.",
            "Unfortunately, my standards raise above you.",
            "My love is exclusive to one other...",
            "Though I'd love to make an exception for you, I can't marry a human.",
            "I'm flattered but no, sweetheart 😘",
            "I'm a robot. I would recommend asking someone else.",
            "Perhaps pick a user with sentience.",
            "There's desperate, and then there's proposing to a bot.",
            "No.",
            "Thanks, but I could do better.",
            "Are you serious? No.",
            "I'm a robot, I'm not interested, and you could do better, sweetheart.",
        ])


    @staticmethod
    def proposing_to_bot(instigator, target):
        '''
        When they propose to another bot
        '''

        return choice([
            "To the best of my knowledge, most robots can't consent.",
            "The majority of robots are incapable of love, I'm afraid.",
            "You can't marry a robot _quite yet_ in this country. Give it a few years.",
            "Robots, although attractive, aren't great spouses.",
        ])


    @staticmethod
    def proposing_to_themselves(instigator, target):
        '''
        When they propose to themselves
        '''

        return choice([
            "That is you. You cannot marry the you.",
            "Are... are you serious? No.",
            "Marriage is a union between two people. You are one people. No.",
            f"{target.mention}, do you accept {instigator.mention}'s proposal?\n... Wait, no, you're the same person. The marriage is off!",
        ])


    @staticmethod
    def accepting_valid_proposal(instigator, target):
        '''
        When the target accepts a proposal from the instigator
        '''

        return choice([
            f"{instigator.mention}, {target.mention}, I now pronounce you married.",
            f"{instigator.mention}, you're now married to {target.mention} c:",
            f"And with that, {instigator.mention} and {target.mention} are partners.",
            f"After all the love and pining, it is done. {instigator.mention}, {target.mention}, you're now married.",
        ])


    @staticmethod
    def declining_valid_proposal(instigator, target):
        '''
        When the target declins a valid proposal from the instigator
        '''

        return choice([
            "That's fair. The marriage has been called off.",
            "Oh boy. The wedding is off. You two talk it out.",
            f"I hate to say it, {instigator.mention}, but they said no...",
            "Oh boy. They said no. That can't be good.",
        ])


    @staticmethod
    def proposal_timed_out(instigator, target):
        '''
        When the instigator's propsal times out
        '''

        return choice([
            f"{instigator.mention}, your proposal has timed out. Try again when they're online!",
            f"Huh. Seems like they didn't respond. Maybe try again later, {instigator.mention}?",
            f"Apparently you aren't even deemed worthy a response. That's rude. Try later, {instigator.mention}.",
        ])


def setup(bot:CustomBot):
    x = MarriageRandomText(bot)
    bot.add_cog(x)
