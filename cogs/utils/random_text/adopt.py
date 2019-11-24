from cogs.utils.random_text.text_template import TextTemplate, get_random_valid_string


class AdoptRandomText(TextTemplate):

    @staticmethod
    @get_random_valid_string
    def valid_target(instigator=None, target=None):
        return [
            "It looks like {instigator.mention} wants to adopt you, {target.mention}. What do you think?",
            "{instigator.mention} wants to be your parent, {target.mention}. What do you say?",
            "{target.mention}, {instigator.mention} is interested in adopting you. How do you feel?",
            "{instigator.mention} wants to adopt you, {target.mention}. Do you accept?",
            "{instigator.mention} wants to share the love and make you their child, {target.mention}. What do you think?",
            "{instigator.mention} would love to adopt you, {target.mention}. What do you think?",
            "{target.mention}, today's your lucky day. {instigator.mention} wants to adopt you. Do you accept?",
            "{target.mention}, {instigator.mention} wants to be your parent. What do you say?",
        ]

    @staticmethod
    @get_random_valid_string
    def target_is_family(instigator=None, target=None):
        return [
            "Sorry but you're already related to them, {instigator.mention}!",
            "You can't adopt someone if you're related to them already.",
            "Laws prohibit adopting someone you're related to already.",
            "You can't adopt a family member!",
        ]

    @staticmethod
    @get_random_valid_string
    def target_is_me(instigator=None, target=None):
        return [
            "I don't think that's appropriate.",
            "I would rather not.",
            "Thank you for the offer, but I'll have to refuse.",
            "No thank you.",
            "I think it best you don't adopt me. No offense.",
            "I have one daddy and one daddy only, sorry. ",
            "Caleb would be pretty upset not gonna lie, so I'm gonna have to decline.",
            "The fee to adopt me is $50. Cough that up monthly and you've got yourself a MarriageBaby, {instigator.mention}.",
            "Sorry but I'd rather not live with trash.",
        ]

    @staticmethod
    @get_random_valid_string
    def target_is_bot(instigator=None, target=None):
        return [
            "I don't think bots can consent to that.",
            "I don't think you can adopt a robot quite yet.",
            "Robots tend to not need parents most of the time.",
            "I think a robot would make a bad child for you.",
            "Pretty sure you have to adopt someone with sentience, {instigator.mention}, why don't you try a different server member?",
            "#BotsAreNotPeopleToo",
        ]

    @staticmethod
    @get_random_valid_string
    def target_is_you(instigator=None, target=None):
        return [
            "You can't adopt yourself, as far as I know.",
            "That's you. You can't adopt the you.",
            "Did you expect me to say yes?",
            "Why did you think that would work?",
            "Stop it. Weirdo.",
        ]

    @staticmethod
    @get_random_valid_string
    def instigator_is_instigator(instigator=None, target=None):
        return [
            "Be patient, {instigator.mention}, wait for a response on your other proposal first!",
            "Woah, slow down, wait for a response on the other proposal first.",
            "You can only make one proposal at a time. Please wait.",
            "I know it's all very exciting but you can only make one proposal at a time.",
            "Wait your turn, you absolute nonce!",
            "Don't be greedy, {instigator.mention}, wait your turn.",
            "Excuse me you soggy waffle, calm the heck town and wait pls and thx.",
        ]

    @staticmethod
    @get_random_valid_string
    def instigator_is_target(instigator=None, target=None):
        return [
            "You need to answer your proposal first.",
            "You can't make any new proposals until you respond to the ones you have already.",
            "You've just been asked out though, you should answer them first.",
            "Please respond to your other proposal first.",
        ]

    @staticmethod
    @get_random_valid_string
    def target_is_instigator(instigator=None, target=None):

        return [
            "They just proposed to someone themself - give it a minute and see how it goes.",
            "You'll have to wait until their own proposal is dealt with.",
            "They asked someone out themself; see what happens with that first.",
            "Please respond to your other proposal first.",
        ]

    @staticmethod
    @get_random_valid_string
    def target_is_target(instigator=None, target=None):
        return [
            "They're a popular choice, aren't they? Give them a minute to respond to their existing proposal.",
            "Looks like someone got there before you - see what they say to that.",
            "I don't mean to start drama but someone already asked them out.",
            "Funnily enough, someone proposed to them already. See what they say to that before you propose yourself.",
        ]

    @staticmethod
    @get_random_valid_string
    def request_timeout(instigator=None, target=None):
        return [
            "Looks like you aren't even deemed a response. That's pretty rude. Try again later, {instigator.mention}!",
            "Apparently they have better things to do than respond to you, {instigator.mention}.",
            "They didn't respond... Ah well. I'll send them back to the orphanage for you, {instigator.mention}.",
            "Turns out they aren't even interested enough to respond, {instigator.mention}. I apologise on their behalf.",
        ]

    @staticmethod
    @get_random_valid_string
    def request_accepted(instigator=None, target=None):
        return [
            "They said yes! I'm happy to introduce {instigator.mention} as your new parent, {target.mention}!",
            "You have a new child, {instigator.mention}! Say hello to {target.mention}~",
            "I'm sure {instigator.mention} will be happy to welcome you into the family, {target.mention}.",
            "WHO'S YOUR DADDY? Or...mommy...or parent...whatever, welcome to {instigator.mention}'s family, {target.mention}.",
        ]

    @staticmethod
    @get_random_valid_string
    def request_denied(instigator=None, target=None):
        return [
            "Looks like they don't want to be your child, {instigator.mention}.",
            "They don't want to, {instigator.mention}. Sorry!",
            "They said no, {instigator.mention}, looks like they won't be your child for now.",
            "Apparently they don't deem you a worthy parent, {instigator.mention}.",
        ]

    @staticmethod
    @get_random_valid_string
    def target_is_unqualified(instigator=None, target=None):
        return [
            "It looks like they have a parent already.",
            "Sorry but they have a parent already!",
            "Looks like they already have a loving(?) parent. Sorry!",
            "Looks like you missed the adoption train, {instigator.mention}, because {target.mention} already has a parent.",
        ]
