from cogs.utils.random_text.text_template import TextTemplate, get_random_valid_string


class EmancipateRandomText(TextTemplate):

    @staticmethod
    @get_random_valid_string
    def valid_target(instigator=None, target=None):
        return [
            "Looks like {instigator.mention} left you, {target.mention}. I'm sorry for your loss.",
            "You're free of {target.mention}, {instigator.mention}!",
            "Say goodbye to {target.mention}, {instigator.mention}! You're parentless now!",
            "Freedom for you, {instigator.mention}!",
            "Have fun living in the streets!",
            "You no longer have a parent.\n... Don't think too hard about it.",
        ]

    @staticmethod
    @get_random_valid_string
    def instigator_is_unqualified(instigator=None, target=None):
        return [
            "You don't actually have a parent. This is awkward.",
            "You're already an orphan though!",
        ]
