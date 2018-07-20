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
[ ] Picking a parent while waiting on a response f[ ] another
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
    return choice([
        f"{target.mention}, do you accept {instigator.mention}'s proposal?",
        f"{target.mention}, {instigator.mention} has proposed to you. What do you say?",
        f"{instigator.mention} may be young, but they're full of heart. Do you want to marry them, {target.mention}?",
        f"{instigator.mention} finally wants to settle down with you, {target.mention}. Do you accept?",
        f"{target.mention}, will you marry {instigator.mention}?",
        f"{instigator.mention} wants you to be the love of their life, {target.mention}. Do you accept?",
    ])


def proposing_to_married(instigator, target):
    return choice([
        f"I hate to tell you this, {instigator.mention}, but they're already married...",
        f"I don't know if you knew this but they're already married, {instigator.mention}...",
        f"Oh, uh, sorry {instigator.mention}, but they're already seeing someone.",
        f"Ah... this is awkward... they already have someone, {instigator.mention}...",
    ])


def proposing_when_married(instigator, target):
    return choice([
        f"Maybe you should wait until after you're divorced, {instigator.mention}.",
        f"You already have someone, {instigator.mention}."
        f"You're not single, {instigator.mention}.",
        f"I hate to rain on your parade, {instigator.mention}, but I don't think that appropriate while you're married already.",
    ])


def proposing_to_family(instigator, target):
    return choice([
        f"That... that's a family member of yours, {instigator.mention}...",
        f"Though we support free speech and all, you can't really marry someone you're related to, {instigator.mention}.",
        f"We've made great strides towards equality recently, {instigator.mention}, but you still can't marry a relative of yours.",
        f"{instigator.mention} you're related to them .-.",
    ])


def proposing_while_waiting(instigator, target):
    return choice([
        f"",
    ])

