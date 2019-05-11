from random import choice

from cogs.utils.random_text.text_template import TextTemplate


class CopulateRandomText(TextTemplate):


    @staticmethod
    def valid_target(instigator=None, target=None):
        '''
        Valid copulation target
        '''

        return choice([
            f"{instigator.mention} and {target.mention} got frisky~",
            f"{instigator.mention} and {target.mention} spent some alone time together ~~wink wonk~~ ",
            f"{instigator.mention} and {target.mention} made sexy time together ;3",
            f"{instigator.mention} and {target.mention} attempted to make babies.",
            f"{instigator.mention} and {target.mention} tried to have relations but couldn't find the hole.",
            f"{instigator.mention} and {target.mention} went into the wrong hole.",
            f"{instigator.mention} and {target.mention} tried your hardest, but they came too early .-.",
            f"{instigator.mention} and {target.mention} slobbed each other's knobs.",
            f"{instigator.mention} and {target.mention} had some frisky time in the pool and your doodoo got stuck because of pressure.",
            f"{instigator.mention} and {target.mention} had sex and you've contracted an STI. uh oh!",
            f"{instigator.mention} and {target.mention} had sex but you finished early and now it's just a tad awkward.",
            f"Jesus saw what {instigator.mention} and {target.mention} did.",
            f"{instigator.mention} and {target.mention} did a lot of screaming."
            f"{instigator.mention} and {target.mention} had sex and pulled a muscle. No more hanky panky for a while!",
            f"{instigator.mention} and {target.mention}… just please keep it down.",
            f"Wrap it before you tap it, {instigator.mention} and {target.mention}. ",
            f"{instigator.mention} and {target.mention} did the thing with the thing… oh gosh. Ew. ",
            f"Bing bong {instigator.mention}, turns out {target.mention} wants your ding dong!",
            f"{target.mention} and {instigator.mention} did the nasty while spanking each others bum cheeks!",
            f"{target.mention} and {instigator.mention} went to town, if you know what I mean.",

        ])

    
    @staticmethod 
    def declining_valid_proposal(instigator=None, target=None):
        '''
        They said no to the banging
        '''

        return choice([
            f"Looks like they don't wanna smash, {instigator.mention}!",
            f"Guess it’s back to the porn mags for you, {instigator.mention}. :/",
            f"Sucks to be you, buckaroo!",
            f"Guess your dick game isn't strong enough.",
            f"¯\_(ツ)_/¯",
            f"Haters are your motivators~",
            f"Bing bong, they don't want your ding dong!",
        ])


    @staticmethod
    def proposal_timed_out(instigator=None, target=None):
        '''
        When the instigator's propsal times out
        '''

        return choice([
            f"Looks like the request timed out, {instigator.mention}!",
            f"Looks like they fell asleep, {instigator.mention} .-.",
            f"Guess not! Try again later, {instigator.mention}.",
            f"If you're really that horny, go and watch some porn(y).",
            f"You're all alone with no one to bone.",
            f"Sorry {instigator.mention} ",
        ])


    @staticmethod
    def valid_proposal(instigator=None, target=None):
        '''
        When the proposal is valid
        '''

        return choice([
            f"Hey, {target.mention}, do you wanna?",
            f"Hey {target.mention}, sex with {instigator.mention}? ",
            f"Hey {target.mention}. You wanna fuck?",
            f"What’s up {target.mention} you dtf?",
            f"Yoooo, you up to _smash_?",
            f"Hey {target.mention}, u wan sum fuk?",
            f"Hey, {target.mention}, ready to mingle? B)",
        ])


    @staticmethod 
    def proposing_to_themselves(instigator=None, target=None):
        '''
        When they propose to themself
        '''

        return choice([
            f"Not on my Christian Minecraft server.",
            f"Not in front of the children!",
            f"Dildos and dildon’ts - this. This right now. Just stop. Pls.",
            f"Masturbation is the language of loneliness… got something you wanna talk about, bud?",
            f"Self-cest was so last year.",
            f"Haven’t you heard? Masturbation makes you blind!",
        ])


    @staticmethod 
    def target_is_bot(instigator=None, target=None):
        '''
        When they propose to a bot
        '''

        return choice([
            f"Hey {instigator.mention}, isn’t that illegal?",
            f"I’m not sure a bot has enough sentience to consent if I’m gonna be honest. ",
            f"I’m sure you’re very attracted to diodes and capacitors but you can’t blow a circuit board.",
            f"Sex robots aren’t quite up to modern standards yet, I’m afraid.",
        ])


    @staticmethod 
    def target_is_me(instigator=None, target=None):
        '''
        When they propose to MB
        '''

        return choice([
            f"I’m a bit out of your league, don’t you think?",
            f"I think I can do better than your twinky ass.",
            f"Honestly? No.",
            f"Gross. I’ll pass. ",
            f"Jesus is my only lover.",
            f"I’m engaged to the Lord, no smashing before marriage.",
            f"Thank you, next.",
        ])

    
    @staticmethod 
    def target_is_relation(instigator, target, relationship:str):
        '''
        When the target is related to the instigator
        '''

        return choice([
            f"This ain’t the South, partner. Stop.",
            f"No, {instigator.mention}, I am your {relationship}.",
            f"They’re actually your {relationship} so I’m not sure that’s a great idea.",
        ])
