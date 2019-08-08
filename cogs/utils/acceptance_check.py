import re as regex

import discord


class AcceptanceCheck(object):
    """A general helper to check if a user is saying yes or no to a given
    proposal"""

    PROPOSAL_YES = regex.compile(r"(i do)|(yes)|(of course)|(definitely)|(absolutely)|(yeah)|(yea)|(sure)|(accept)", regex.IGNORECASE)
    PROPOSAL_NO = regex.compile(r"(i don't)|(i dont)|(no)|(to think)|(i'm sorry)|(im sorry)", regex.IGNORECASE)

    def __init__(self, target_id:int, channel_id:int=None):
        self.target_id = target_id
        self.channel_id = channel_id

    def check(self, message:discord.Message):
        """The check that should be passed to a bot.wait_for method"""

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
