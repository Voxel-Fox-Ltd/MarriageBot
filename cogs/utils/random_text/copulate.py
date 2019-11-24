from cogs.utils.random_text.text_template import TextTemplate, get_random_valid_string


class CopulateRandomText(TextTemplate):

    @staticmethod
    @get_random_valid_string
    def request_accepted(instigator=None, target=None):
        return [
            "{instigator.mention} and {target.mention} got frisky~",
            "{instigator.mention} and {target.mention} spent some alone time together ~~wink wonk~~",
            "{instigator.mention} and {target.mention} made sexy time together ;3",
            "{instigator.mention} and {target.mention} attempted to make babies.",
            "{instigator.mention} and {target.mention} tried to have relations but couldn't find the hole.",
            "{instigator.mention} and {target.mention} went into the wrong hole.",
            "{instigator.mention} and {target.mention} tried their hardest, but they came too early .-.",
            "{instigator.mention} and {target.mention} slobbed each other's knobs.",
            "{instigator.mention} and {target.mention} had some frisky time in the pool and your doodoo got stuck because of pressure.",
            "{instigator.mention} and {target.mention} had sex and you've contracted an STI. uh oh!",
            "{instigator.mention} and {target.mention} had sex but you finished early and now it's just a tad awkward.",
            "Jesus saw what {instigator.mention} and {target.mention} did.",
            "{instigator.mention} and {target.mention} did a lot of screaming.",
            "{instigator.mention} and {target.mention} had sex and pulled a muscle. No more hanky panky for a while!",
            "{instigator.mention} and {target.mention}… just please keep it down.",
            "Wrap it before you tap it, {instigator.mention} and {target.mention}.",
            "{instigator.mention} and {target.mention} did the thing with the thing… oh gosh. Ew.",
            "Bing bong {instigator.mention}, turns out {target.mention} wants your ding dong!",
            "{target.mention} and {instigator.mention} did the nasty while spanking each others bum cheeks!",
            "{target.mention} and {instigator.mention} went to town, if you know what I mean.",
            "{target.mention} and {instigator.mention} got it on. I sure hope Jesus consented, too…",
            "JESUS CONSENTS, GOD WILLS IT.",
            "{target.mention} and {instigator.mention} are getting freaky, looks like they aren’t afraid to show the pie.",
            "{target.mention} and {instigator.mention} are fucking like rabbits, looks like they broke the bed. A new bed will be needed.",
            "{target.mention} bends over {instigator.mention} and fucks them raw. ",
            "{target.mention} pushes {instigator.mention} against the wall, choking them and fucking them silly.",
            "{target.mention} fucks {instigator.mention} in the ass, but they accidentally shit the bed.",
            "{target.mention} fucks {instigator.mention} vigorously with a dildo! Jackhammer!",
            "{target.mention} plows {instigator.mention} into the couch before spraying {instigator.mention} with their semen!",
        ]

    @staticmethod
    @get_random_valid_string
    def request_denied(instigator=None, target=None):
        return [
            "Looks like they don't wanna smash, {instigator.mention}!",
            "Guess it's back to the porn mags for you, {instigator.mention}. :/",
            "Sucks to be you, buckaroo!",
            "Guess your dick game isn't strong enough.",
            "¯\\_(ツ)_/¯",
            "Haters are your motivators~",
            "Bing bong, they don't want your ding dong!",
            "No means no. Sorry!",
            "I'd love to, but I'm going to have a migraine that night.",
            "I think I hear someone calling me... way, way over there. *poofs* Sorry {instigator.mention}.",
            "Like right now? I don't think that's a great idea, what with my infectious mouth disease and all...",
            "This feels like the beginning of a really great friendship! Ouch.. Friendzoned.",
            "It's not you; it's your facial hair. And your shirt. And your personality.",
            "I'd fuck you, but I'd be afraid of my future children inheriting your face",
            "Oh, wait, I think I just spotted someone else that I'd rather be talking to! That has to sting...",
        ]

    @staticmethod
    @get_random_valid_string
    def proposal_timed_out(instigator=None, target=None):
        return [
            "Looks like the request timed out, {instigator.mention}!",
            "Looks like they fell asleep, {instigator.mention} .-.",
            "Guess not! Try again later, {instigator.mention}.",
            "If you're really that horny, go and watch some porn(y).",
            "You're all alone with no one to bone.",
            "Sorry {instigator.mention}",
            "¯\\_(ツ)_/¯ {instigator.mention}",
            "Seems they got cold feet! Sorry buddy!",
        ]

    @staticmethod
    @get_random_valid_string
    def valid_target(instigator=None, target=None):
        return [
            "Hey, {target.mention}, do you wanna?",
            "Hey {target.mention}, sex with {instigator.mention}? ",
            "Hey {target.mention}. You wanna fuck?",
            "What's up {target.mention} you dtf?",
            "Yoooo, you up to _smash_?",
            "Hey {target.mention}, u wan sum fuk?",
            "Hey, {target.mention}, ready to mingle? B)",
            "Fuck me Daddy? ",
            "H-hi *playfully plays with your shirt* m-my princess pa- parts tingle.",
            "Roses are red, Violets are blue, I suck at poems, let's fuck.",
            "What's the drop rate on your panties?",
        ]

    @staticmethod
    @get_random_valid_string
    def proposing_to_themselves(instigator=None, target=None):
        return [
            "Not on my Christian Minecraft server.",
            "Not in front of the children!",
            "Dildos and dildon'ts - this. This right now. Just stop. Pls.",
            "Masturbation is the language of loneliness… got something you wanna talk about, bud?",
            "Self-cest was so last year.",
            "Haven't you heard? Masturbation makes you blind!",
        ]

    @staticmethod
    @get_random_valid_string
    def target_is_bot(instigator=None, target=None):
        return [
            "Hey {instigator.mention}, isn't that illegal?",
            "I'm not sure a bot has enough sentience to consent if I'm gonna be honest. ",
            "I'm sure you're very attracted to diodes and capacitors but you can't blow a circuit board.",
            "Sex robots aren't quite up to modern standards yet, I'm afraid.",
        ]

    @staticmethod
    @get_random_valid_string
    def target_is_me(instigator=None, target=None):
        return [
            "I'm a bit out of your league, don't you think?",
            "I think I can do better than your twinky ass.",
            "Honestly? No.",
            "Gross. I'll pass. ",
            "Jesus is my only lover.",
            "I'm engaged to the Lord, no smashing before marriage.",
            "Thank you, next.",
            "STRANGER DANGER!",
            "Sure, go ahead if you want to make me short circuit, that's *perfectly* fine.",
            "My daddy said no I'm sorry.",
            "#Binch is the only relationship I'm interested in, sorry.",
        ]

    @staticmethod
    @get_random_valid_string
    def target_is_relation(instigator=None, target=None):
        return [
            "This ain't the South, partner. Stop.",
            "Don't turn the family tree into a family donut.",
            "That's gross, {instigator.mention} please reconsider.",
        ]
