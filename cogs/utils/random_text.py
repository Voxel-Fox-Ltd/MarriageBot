'''
Simple generation of random text for any occasion the bot might have to talk.
Variety is the spice of life.
'''

from random import choice


'''
Events:
[x] Proposing to a person
[x] Proposing to a married person
[x] Proposing when married
[x] Proposing to a person in your family
[ ] Proposing while having proposed to someone else
[ ] Proposing while they've been proposed to
[ ] Proposing to the bot
[ ] Proposing to a different bot
[ ] Proposing to yourself
[ ] Accepting a proposal
[ ] Declining a proposal
[ ] Proposal timing out

[ ] Picking a parent
[ ] Picking a family member as a parent
[ ] Picking the bot as your parent
[ ] Picking a parent while waiting on a response from another
[ ] Picking a parent while they've already been asked
[ ] Picking a different bot as your parent
[ ] Picking yourself as your parent
[ ] Parent request timing out
[ ] Accepting request
[ ] Declining request
[ ] Request times out

[ ] Divorcing your partner
[ ] Divorcing someone who isn't your partner

[ ] Disown your child
[ ] Disown someone who isn't your child

[ ] No family tree
'''

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


def proposing_to_married(instigator, target):
    '''
    When you're proposing to a married person
    '''

    return choice([
        f"I hate to tell you this, {instigator.mention}, but they're already married...",
        f"I don't know if you knew this but they're already married, {instigator.mention}...",
        f"Oh, uh, sorry {instigator.mention}, but they're already seeing someone.",
        f"Ah... this is awkward... they already have someone, {instigator.mention}...",
    ])


def proposing_when_married(instigator, target):
    '''
    When you make a proposal while married
    '''

    return choice([
        f"Maybe you should wait until after you're divorced, {instigator.mention}.",
        f"You already have someone, {instigator.mention}."
        f"You're not single, {instigator.mention}.",
        f"I hate to rain on your parade, {instigator.mention}, but I don't think that appropriate while you're married already.",
    ])


def proposing_to_family(instigator, target):
    '''
    When you propose to a family member
    '''

    return choice([
        f"That... that's a family member of yours, {instigator.mention}...",
        f"Though we support free speech and all, you can't really marry someone you're related to, {instigator.mention}.",
        f"We've made great strides towards equality recently, {instigator.mention}, but you still can't marry a relative of yours.",
        f"{instigator.mention} you're related to them .-.",
    ])


def proposing_while_waiting(instigator, target):
    '''
    When you propose while you're already waiting on a response from another proposal
    '''

    return choice([
        f"",
    ])


def proposing_when_theyre_popular(instigator, target):
    '''
    When you propose while they're yet to respond to another proposal
    '''

    return choice([])


def proposing_to_me(instigator, target):
    '''
    When they propose to the bot
    '''

    return choice([])


def proposing_to_bot(instigator, target):
    '''
    When they propose to another bot
    '''

    return choice([])


def proposing_to_themselves(instigator, target):
    '''
    When they propose to themselves
    '''

    return choice([])


def accepting_valid_proposal(instigator, target):
    '''
    When the target accepts a proposal from the instigator
    '''

    return choice([])


def declining_valid_proposal(instigator, target):
    '''
    When the target declins a valid proposal from the instigator
    '''

    return choice([])


def proposal_timed_out(instigator, target):
    '''
    When the instigator's propsal times out
    '''

    return choice([])


def valid_parent_choice(instigator, target):
    '''
    When the instigator asks the target to be their parent
    '''

    return choice([])


def parent_is_family(instigator, target):
    '''
    When the instigator picks the target as a parent but they're already family members
    '''

    return choice([])


def parent_is_me(instigator, target):
    '''
    The instigator picked the bot as a parent
    '''

    return choice([])


def parent_is_bot(instigator, target):
    '''
    The instigator wants to parentify a bot
    '''

    return choice([])


def parent_ask_multiple(instigator, target):
    '''
    When the instigator asks the target to be their parent while they've already asked another
    '''

    return choice([])

