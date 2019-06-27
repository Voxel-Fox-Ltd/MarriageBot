from random import choice

from cogs.utils.random_text.text_template import TextTemplate


class MakeParentRandomText(TextTemplate):


    @classmethod
    def valid_target(cls, instigator=None, target=None):
        '''
        When the instigator asks the target to be their parent
        '''

        return choice(cls.get_valid_strings([
            "{instigator.mention} wants to be your child, {target.mention}. Do you accept?",
            "{instigator.mention} is willing to give their love to you and make you their parent, {target.mention}. What do you say?",
            "{instigator.mention} would love to be adopted by you, {target.mention}. What do you think?",
            "Today could be your day, {instigator.mention}. {target.mention}, will you adopt them?",
            "{target.mention}, {instigator.mention} wants to be your child. What do you say?",
            "{target.mention}, do you want to be {instigator.mention}'s parent?",
        ], *['instigator' if instigator else None, 'target' if target else None])).format(instigator=instigator, target=target)


    @classmethod
    def target_is_family(cls, instigator=None, target=None):
        '''
        When the instigator picks the target as a parent but they're already family members
        '''

        return choice(cls.get_valid_strings([
            "They're already part of the family you're in, {instigator.mention}.",
            "You can't just mess up your family tree like that - you're already related to that person, {instigator.mention}.",
            "Family trees tend to get messed up when you get relations like that, so I'm gonna have to say no, {instigator.mention}.",
            "{instigator.mention}, they're already part of your family.",
        ], *['instigator' if instigator else None, 'target' if target else None])).format(instigator=instigator, target=target)


    @classmethod
    def target_is_me(cls, instigator=None, target=None):
        '''
        The instigator picked the bot as a parent
        '''

        return choice(cls.get_valid_strings([
            "I'm afraid I'll have to decline, but thank you for the offer.",
            "Not that I don't _like_ you or anything, but I would rather not.",
            "You can't adopt any robots, me included. Sorry!",
            "Though I'd love to, I can't.",
            "I'm sure I'd be a wonderful child, but I can't set you as my child.",
            "Thanks for the offer, but no thank you.",
        ], *['instigator' if instigator else None, 'target' if target else None])).format(instigator=instigator, target=target)


    @classmethod
    def target_is_bot(cls, instigator=None, target=None, give_text:bool=False):
        '''
        The instigator wants to parentify a bot
        '''

        if not give_text:
            return False  # Used for the text_template process

        return choice(cls.get_valid_strings([
            "Bots don't make _terribly_ good parents, but I'll allow it, {instigator.mention}. Have fun with your new family!",
            "Though robots often have trouble with love, I'm sure {target.mention} will make a lovely parent for you, {instigator.mention}.",
            "Your choice of robot is... interesting. {target.mention} is now your parent, {instigator.mention}!",
            "A robot probably isn't the best choice, but who am I to judge? Have fun with your new family, {instigator.mention}!",
        ], *['instigator' if instigator else None, 'target' if target else None])).format(instigator=instigator, target=target)


    @classmethod
    def instigator_is_instigator(cls, instigator=None, target=None):
        '''
        When the instigator asks the target to be their parent while they've already asked another
        '''

        return choice(cls.get_valid_strings([
            "Hold your horses, {instigator.mention}, you've already made a proposition to someone.",
            "Slow down a bit - wait for a response to your other question.",
            "Though I hate to rain on your parade, you can only make one proposition at a time.",
            "Chill. One proposal at a time, {instigator.mention}.",
            "You can only make or recieve one proposition at a time.",
        ], *['instigator' if instigator else None, 'target' if target else None])).format(instigator=instigator, target=target)


    @classmethod
    def target_is_instigator(cls, instigator=None, target=None):
        '''
        When the person you're responding to asked someone out
        '''

        return choice(cls.get_valid_strings([
            "They've just proposed to someone. Give it a minute.",
            "Give them a minute to deal with their proposal and then try again.",
            "Looks like they're focused on something else right now. Try again in a minute.",
            "Holdup, {instigator.mention}, they've just proposed to someone else.",
        ], *['instigator' if instigator else None, 'target' if target else None])).format(instigator=instigator, target=target)


    @classmethod
    def instigator_is_target(cls, instigator=None, target=None):
        '''
        When the instigator has another proposal to respond to
        '''

        return choice(cls.get_valid_strings([
            "Shouldn't you respond to your other question first, {instigator.mention}?",
            "I think you should prioritise your other proposal, {instigator.mention}.",
            "You've already been asked something, {instigator.mention} - you should deal with that first.",
            "You can only make or recieve one proposition at a time.",
        ], *['instigator' if instigator else None, 'target' if target else None])).format(instigator=instigator, target=target)


    @classmethod
    def target_is_target(cls, instigator=None, target=None):
        '''
        When the target is also someone elses' target
        '''

        return choice(cls.get_valid_strings([
            "Oops, looks like someone else asked first. Just wait a minute and see what they say.",
            "Someone already made a proposition to them, try again in a minute.",
            "Looks like you'll need to wait until they respond to your current offer.",
            "Unfotrunately they need to respond to their current proposal before you can make yours.",
        ], *['instigator' if instigator else None, 'target' if target else None])).format(instigator=instigator, target=target)


    @classmethod
    def target_is_you(cls, instigator=None, target=None):
        '''
        Picking yourself as your parent
        '''

        return choice(cls.get_valid_strings([
            "Oh, ha ha, very funny.",
            "I'm not super sure why you thought that would work.",
            "Try picking someone that isn't yourself next time!",
            "Oddly enough, you can't adopt yourself. I wonder why that is?",
            "You can't adopt yourself, I'm sorry to say.",
        ], *['instigator' if instigator else None, 'target' if target else None])).format(instigator=instigator, target=target)


    @classmethod
    def instigator_is_unqualified(cls, instigator=None, target=None):
        '''
        Picking a parent while you already have one
        '''

        return choice(cls.get_valid_strings([
            "I know it's a strange setup, but you can only pick one of your parents, {instigator.mention}.",
            "You have a parent already, {instigator.mention}.",
            "You can only have one parent at a time, as odd as that sounds, {instigator.mention}.",
            "You can't pick a new parent while you already have one, {instigator.mention}.",
        ], *['instigator' if instigator else None, 'target' if target else None])).format(instigator=instigator, target=target)


    @classmethod
    def request_timeout(cls, instigator=None, target=None):
        '''
        Parent request timed out
        '''

        return choice(cls.get_valid_strings([
            "Sorry, {instigator.mention}, but back to the orphanage with you.",
            "No response from your decided daddy, {instigator.mention}. Sorry about that.",
            "No response. Huh. Guess you'll have to remain parentless for now, {instigator.mention}.",
            "Ouch. No response. Sorry, {instigator.mention}. I'll take you out for ice cream later.",
            "They didn't seem to say anything, {instigator.mention}. Maybe try again later!",
            "Sorry to say this, {instigator.mention}, but they didn't get back in time to respond.",
            "{instigator.mention}, your parent request has timed out. Try again when they're online!",
        ], *['instigator' if instigator else None, 'target' if target else None])).format(instigator=instigator, target=target)


    @classmethod
    def request_accepted(cls, instigator=None, target=None):
        '''
        Accepted parent request
        '''

        return choice(cls.get_valid_strings([
            "{instigator.mention}, meet your new parent, {target.mention}!",
            "{target.mention}, you have sucessfully adopted {instigator.mention}!",
            "I'm happy to introduce {instigator.mention} to the {target.mention} family!",
            "They accepted, {instigator.mention}! Welcome to the new family.",
            "{instigator.mention}, your new parent is {target.mention} c:",
        ], *['instigator' if instigator else None, 'target' if target else None])).format(instigator=instigator, target=target)


    @classmethod
    def request_denied(cls, instigator=None, target=None):
        '''
        When the parent request is denied
        '''

        return choice(cls.get_valid_strings([
            "Sorry, {instigator.mention}, but they said no.",
            "Unfortunately they said no, {instigator.mention}. Better luck next time!",
            "It seems they aren't ready to be your parent, {instigator.mention}.",
        ], *['instigator' if instigator else None, 'target' if target else None])).format(instigator=instigator, target=target)
