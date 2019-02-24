from random import choice

from discord.ext.commands import Cog

from cogs.utils.custom_bot import CustomBot


class AdoptRandomText(Cog):

    def __init__(self, bot:CustomBot):
        self.bot = bot


    @staticmethod
    def valid_target(instigator, target):
        '''
        Valid adoption target
        '''

        return choice([
            f"It looks like {instigator.mention} wants to adopt you, {target.mention}. What do you think?",
            f"{instigator.mention} wants to be your parent, {target.mention}. What do you say?",
            f"{target.mention}, {instigator.mention} is interested in adopting you. How do you feel?",
            f"{instigator.mention} wants to adopt you, {target.mention}. Do you accept?",
            f"{instigator.mention} wants to share the love and make you their child, {target.mention}. What do you think?",
            f"{instigator.mention} would love to adopt you, {target.mention}. What do you think?",
            f"{target.mention}, today's your lucky day. {instigator.mention} wants to adopt you. Do you accept?",
            f"{target.mention}, {instigator.mention} wants to be your parent. What do you say?",
        ])


    @staticmethod
    def target_is_family(instigator, target):
        '''
        The given target is already in the instigator's family
        '''

        return choice([
            f"Sorry but you're already related to them, {instigator.mention}!",
            "You can't adopt someone if you're related to them already.",
            "Laws prohibit adopting someone you're related to already.",
            "You can't adopt a family member!",
        ])


    @staticmethod
    def target_is_me(instigator, target):
        '''
        They want to adopt the bot
        '''

        return choice([
            "I don't think that's appropriate.",
            "I would rather not.",
            "Thank you for the offer, but I'll have to refuse.",
            "No thank you.",
            "I think it best you don't adopt me. No offense.",
        ])


    @staticmethod
    def target_is_bot(instigator, target):
        '''
        They want to adopt ToddBot
        '''

        return choice([
            "I don't think bots can consent to that.",
            "I don't think you can adopt a robot quite yet.",
            "Robots tend to not need parents most of the time.",
            "I think a robot would make a bad child for you.",
        ])


    @staticmethod
    def target_is_you(instigator, target):
        '''
        They want to adopt themself
        '''

        return choice([
            "You can't adopt yourself, as far as I know.",
            "That's you. You can't adopt the you.",
            "Did you expect me to say yes?",
            "Why did you think that would work?"
        ])


    @staticmethod
    def instigator_is_instigator(instigator, target):
        '''
        They already asked someone out
        '''

        return choice([
            f"Be patient, {instigator.mention}, wait for a response on your other proposal first!",
            "Woah, slow down, wait for a response on the other proposal first.",
            "You can only make one proposal at a time. Please wait.",
            "I know it's all very exciting but you can only make one proposal at a time."
        ])


    @staticmethod
    def instigator_is_target(instigator, target):
        '''
        They need to respond to a proposal first
        '''

        return choice([
            "You need to answer your proposal first.",
            "You can't make any new proposals until you respond to the ones you have already.",
            "You've just been asked out though, you should answer them first.",
            "Please respond to your other proposal first.",
        ])


    @staticmethod
    def target_is_instigator(instigator, target):
        '''
        The person they asked out just asked someone out
        '''

        return choice([
            "They just proposed to someone themself - give it a minute and see how it goes.",
            "You'll have to wait until their own proposal is dealt with.",
            "They asked someone out themself; see what happens with that first.",
        ])


    @staticmethod
    def target_is_target(instigator, target):
        '''
        The person they asked out is already a target
        '''

        return choice([
            "They're a popular choice, aren't they? Give them a minute to respond to their existing proposal.",
            "Looks like someone got there before you - see what they say to that.",
            "I don't mean to start drama but someone already asked them out.",
            "Funnily enough, someone proposed to them already. See what they say to that before you propose yourself.",
        ])


    @staticmethod
    def request_timeout(instigator, target):
        '''
        '''

        return choice([
            f"Looks like you aren't even deemed a response. That's pretty rude. Try again later, {instigator.mention}!",
            f"Apparently they have better things to do than respond to you, {instigator.mention}.",
            f"They didn't respond... Ah well. I'll send them back to the orphanage for you, {instigator.mention}.",
            f"Turns out they aren't even interested enough to respond, {instigator.mention}. I apologise on their behalf.",
        ])


    @staticmethod
    def request_accepted(instigator, target):
        '''
        '''

        return choice([
            f"They said yes! I'm happy to introduce {instigator.mention} as your new parent, {target.mention}!",
            f"You have a new child, {instigator.mention}! Say hello to {target.mention}~",
            f"I'm sure {instigator.mention} will be happy to welcome you into the family, {target.mention}.",
        ])


    @staticmethod
    def request_denied(instigator, target):
        '''
        '''

        return choice([
            f"Looks like they don't want to be your child, {instigator.mention}.",
            f"They don't want to, {instigator.mention}. Sorry!",
            f"They said no, {instigator.mention}, looks like they won't be your child for now.",
            f"Apparently they don't deem you a worthy parent, {instigator.mention}."
        ])


    @staticmethod
    def target_is_unqualified(instigator, target):
        '''
        The target specified already has a parent
        '''

        return choice([
            "It looks like they have a parent already.",
            "Sorry but they have a parent already!",
            "Looks like they already have a loving(?) parent. Sorry!"
        ])


def setup(bot:CustomBot):
    x = AdoptRandomText(bot)
    bot.add_cog(x)
