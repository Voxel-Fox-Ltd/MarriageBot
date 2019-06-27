from random import choice

from cogs.utils.random_text.text_template import TextTemplate


class ProposeRandomText(TextTemplate):


    @classmethod
    def valid_target(cls, instigator=None, target=None):
        '''
        When you make a valid proposal
        '''

        return choice(cls.get_valid_strings([
            "{target.mention}, do you accept {instigator.mention}'s proposal?",
            "{target.mention}, {instigator.mention} has proposed to you. What do you say?",
            "{instigator.mention} may be young, but they're full of heart. Do you want to marry them, {target.mention}",
            "{instigator.mention} finally wants to settle down with you, {target.mention}. Do you accept?",
            "{target.mention}, will you marry {instigator.mention}?",
            "{instigator.mention} wants you to be the love of their life, {target.mention}. Do you accept?",
            "{instigator.mention} has got a nice big ring for you, {target.mention}. What do you say?",
            "{instigator.mention} liked it so they want to put a ring on it...do you accept, {target.mention}?",
            "{instigator.mention} longs for a married life together with {target.mention}. Do you share this fantasy, {target.mention}?",
            "{target.mention}, you be the jelly in my peanut butter and jelly sandwich?",
            "{target.mention}, {instigator.mention} wants to marry you. Will you accept?",
            "I hear wedding bells chiming, {target.mention}! Do you?",
            "Oh boy, {target.mention}, I can sense big things in your future. Will you say yes to marrying {instigator.mention}?",
            "Would you like to marry {instigator.mention}, {target.mention}?",
            "Whether it’ll last forever starts with one question: {target.mention}, would you like to marry {instigator.mention}?",
            "You know the drill: {target.mention}, marry {instigator.mention}?",
            "Commitment starts with a question. {target.mention}, will you marry {instigator.mention}?",
            "Yo {target.mention}, you down to marry {instigator.mention}?",
            "Hey {target.mention} it’s time to get _intimate_~ Do you wanna marry {instigator.mention}?",
            "Hey {target.mention} I dare you to marry {instigator.mention} ;3",
            "{target.mention}, you ready to uwu over {instigator.mention}? ",
            "Hey {target.mention}, are you free tomorrow night? If so, you should get dinner with {instigator.mention} or maybe marry them or something idk.",
            "Could {target.mention} and {instigator.mention} make a cuter married couple than Ollie and Caleb? They sure can try! c;",
            "Wouldn’t {target.mention} and {instigator.mention} look cute as wedding cake toppers? Let’s make it happen!",
            "Hey {target.mention}, wanna marry {instigator.mention} and achieve tumblr crackship fame?",
            "Does anyone ever daydream about {target.mention} snuggling {instigator.mention} in the moonlight?",
            "{instigator.mention} and {target.mention} together? I don’t see it myself, but what does {target.mention} have to say?",
            "{instigator.mention} and {target.mention}? Oh boy I can already see their adopted children! {target.mention}, what do you say?",
        ], *['instigator' if instigator else None, 'target' if target else None])).format(instigator=instigator, target=target)


    @classmethod
    def target_is_unqualified(cls, instigator=None, target=None):
        '''
        When you're proposing to a married person
        '''

        return choice(cls.get_valid_strings([
            "I hate to tell you this, {instigator.mention}, but they're already married...",
            "I don't know if you knew this but they're already married, {instigator.mention}...",
            "Oh, uh, sorry {instigator.mention}, but they're already seeing someone.",
            "Ah... this is awkward... they already have someone, {instigator.mention}...",
            "Polygamy is much harder to store in a database, {instigator.mention}. My apologies.",
            "They're already married, m8. Suck it up and move on.",
            "They’re already with someone - don’t know if you knew.",
            "Unfortunately they found someone they liked more than you. Sorry!",
            "As crazy a concept as this may sound, monogamy is the way I roll.",
            "Poor unfortunate soul… they found someone before you got to them. ",
        ], *['instigator' if instigator else None, 'target' if target else None])).format(instigator=instigator, target=target)


    @classmethod
    def instigator_is_unqualified(cls, instigator=None, target=None):
        '''
        When you make a proposal while married
        '''

        return choice(cls.get_valid_strings([
            "Maybe you should wait until after you're divorced, {instigator.mention}.",
            "You already have someone, {instigator.mention}."
            "You're not single, {instigator.mention}.",
            "I hate to rain on your parade, {instigator.mention}, but I don't think that appropriate while you're married already.",
            "Polygamy is much harder to store in a database, {instigator.mention}. My apologies.",
            "Unfortunately I can't show family trees with polygamy in them, {instigator.mention}.",
        ], *['instigator' if instigator else None, 'target' if target else None])).format(instigator=instigator, target=target)


    @classmethod
    def target_is_family(cls, instigator=None, target=None):
        '''
        When you propose to a family member
        '''

        return choice(cls.get_valid_strings([
            "That... that's a family member of yours, {instigator.mention}...",
            "Though we support free speech and all, you can't really marry someone you're related to, {instigator.mention}.",
            "We've made great strides towards equality recently, {instigator.mention}, but you still can't marry a relative of yours.",
            "{instigator.mention} you're related to them .-.",
            "Incestuous relationships tend to mess up the family tree, so I'm afraid I'll have to say no, {instigator.mention}.",
        ], *['instigator' if instigator else None, 'target' if target else None])).format(instigator=instigator, target=target)


    @classmethod
    def instigator_is_instigator(cls, instigator=None, target=None):
        '''
        When you propose while you're already waiting on a response from another proposal
        '''

        return choice(cls.get_valid_strings([
            "You've already proposed to someone, {instigator.mention}, just wait for a response.",
            "You can only make one proposal at a time, {instigator.mention}.",
            "One proposal at a time is the max limit, {instigator.mention}.",
            "Calm it, {instigator.mention}, you already proposed to someone!",
        ], *['instigator' if instigator else None, 'target' if target else None])).format(instigator=instigator, target=target)


    @classmethod
    def instigator_is_target(cls, instigator=None, target=None):
        '''
        When you propose while they're yet to respond to another proposal
        '''

        return choice(cls.get_valid_strings([
            "Sorry but you've gotta answer your current proposal before you can make one of your own.",
            "You need to answer the proposal you have already before you can make a new one.",
            "You've been proposed to already, {instigator.mention}. Please respond before moving on.",
            "Don't you want to answer the proposal you have already?",
            "Someone already proposed to you though! Answer them first, {instigator.mention}.",
        ], *['instigator' if instigator else None, 'target' if target else None])).format(instigator=instigator, target=target)


    @classmethod
    def target_is_instigator(cls, instigator=None, target=None):
        '''
        When they propose to someone who's already proposed to someone
        '''

        return choice(cls.get_valid_strings([
            "I'm afraid they've already proposed to someone. Give it a minute - see how it goes.",
            "They seem to have just proposed to someone. See how that goes before you try yourself.",
            "Hold your horses - they've just proposed to someone else.",
            "They're waiting on a response from soneone else; give it a minute.",
            "I think they're interested in someone else, having just proposed to them.",
        ], *['instigator' if instigator else None, 'target' if target else None])).format(instigator=instigator, target=target)


    @classmethod
    def target_is_target(cls, instigator=None, target=None):
        '''
        When they propose to someone who's yet to respond to another
        '''

        return choice(cls.get_valid_strings([
            "They're a popular choice, I see. Wait to see what they say to the other proposal they have before trying yourself.",
            "Someone just proposed to them. See what they say there first.",
            "Woah, hold on a minute - someone else proposed first. I wonder what they'll say...",
        ], *['instigator' if instigator else None, 'target' if target else None])).format(instigator=instigator, target=target)


    @classmethod
    def target_is_me(cls, instigator=None, target=None):
        '''
        When they propose to the bot
        '''

        return choice(cls.get_valid_strings([
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
        ], *['instigator' if instigator else None, 'target' if target else None])).format(instigator=instigator, target=target)


    @classmethod
    def target_is_bot(cls, instigator=None, target=None):
        '''
        When they propose to another bot
        '''

        return choice(cls.get_valid_strings([
            "To the best of my knowledge, most robots can't consent.",
            "The majority of robots are incapable of love, I'm afraid.",
            "You can't marry a robot _quite yet_ in this country. Give it a few years.",
            "Robots, although attractive, aren't great spouses.",
        ], *['instigator' if instigator else None, 'target' if target else None])).format(instigator=instigator, target=target)


    @classmethod
    def target_is_you(cls, instigator=None, target=None):
        '''
        When they propose to themselves
        '''

        return choice(cls.get_valid_strings([
            "That is you. You cannot marry the you.",
            "Are... are you serious? No.",
            "Marriage is a union between two people. You are one people. No.",
            "{target.mention}, do you accept {instigator.mention}'s proposal?\n... Wait, no, you're the same person. The marriage is off!",
        ], *['instigator' if instigator else None, 'target' if target else None])).format(instigator=instigator, target=target)


    @classmethod
    def request_accepted(cls, instigator=None, target=None):
        '''
        When the target accepts a proposal from the instigator
        '''

        return choice(cls.get_valid_strings([
            "{instigator.mention}, {target.mention}, I now pronounce you married.",
            "{instigator.mention}, you're now married to {target.mention} c:",
            "And with that, {instigator.mention} and {target.mention} are partners.",
            "After all the love and pining, it is done. {instigator.mention}, {target.mention}, you're now married.",
        ], *['instigator' if instigator else None, 'target' if target else None])).format(instigator=instigator, target=target)


    @classmethod
    def request_denied(cls, instigator=None, target=None):
        '''
        When the target declins a valid proposal from the instigator
        '''

        return choice(cls.get_valid_strings([
            "That's fair. The marriage has been called off.",
            "Oh boy. The wedding is off. You two talk it out.",
            "I hate to say it, {instigator.mention}, but they said no...",
            "Oh boy. They said no. That can't be good.",
            "Maybe a night in a cheap motel with you, but marriage is too much commitment for `{target!s}`.",
            "Roses are red,\nViolets are blue,\nIt looks like they don't want to be with you, {instigator.mention}.",
        ], *['instigator' if instigator else None, 'target' if target else None])).format(instigator=instigator, target=target)


    @classmethod
    def request_timeout(cls, instigator=None, target=None):
        '''
        When the instigator's propsal times out
        '''

        return choice(cls.get_valid_strings([
            "{instigator.mention}, your proposal has timed out. Try again when they're online!",
            "Huh. Seems like they didn't respond. Maybe try again later, {instigator.mention}?",
            "Apparently you aren't even deemed worthy a response. That's rude. Try later, {instigator.mention}.",
        ], *['instigator' if instigator else None, 'target' if target else None])).format(instigator=instigator, target=target)
