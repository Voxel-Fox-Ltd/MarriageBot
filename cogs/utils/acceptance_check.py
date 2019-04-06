from re import compile as _compile, IGNORECASE

from discord import Message


class AcceptanceCheck(object):
    
    PROPOSAL_YES = _compile(r"(i do)|(yes)|(of course)|(definitely)|(absolutely)|(yeah)|(yea)|(sure)|(accept)", IGNORECASE)
    PROPOSAL_NO = _compile(r"(i don't)|(i dont)|(no)|(to think)|(i'm sorry)|(im sorry)", IGNORECASE)

    def __init__(self, target_id:int, channel_id:int=None):
        self.target_id = target_id 
        self.channel_id = channel_id


    def check(self, message:Message):
        '''The check to be passed over to wait_for'''

        # Check it's the right user
        if message.author.id != self.target_id:
            return False

        # Check it's the right channel
        if self.channel_id and message.channel.id != self.channel_id:
            return False

        # Run the regex
        no_regex = self.PROPOSAL_NO.search(message.content)
        yes_regex = self.PROPOSAL_YES.search(message.content)

        # Return the right stuff
        if any([yes_regex, no_regex]):
            return 'NO' if no_regex else 'YES' # Both of these are truthy
        return False
