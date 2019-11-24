from cogs.utils.random_text.text_template import TextTemplate, random_string_class_decorator


@random_string_class_decorator
class EmancipateRandomText(TextTemplate):

    @staticmethod
    def valid_target():
        return [
            "Looks like {instigator.mention} left you, {target.mention}. I'm sorry for your loss.",
            "You're free of {target.mention}, {instigator.mention}!",
            "Say goodbye to {target.mention}, {instigator.mention}! You're parentless now!",
            "Freedom for you, {instigator.mention}!",
            "Have fun living in the streets!",
            "You no longer have a parent.\n... Don't think too hard about it.",
        ]

    @staticmethod
    def instigator_is_unqualified():
        return [
            "You don't actually have a parent. This is awkward.",
            "You're already an orphan though!",
        ]
