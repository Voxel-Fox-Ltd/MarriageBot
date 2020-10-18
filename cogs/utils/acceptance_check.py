import asyncio
import re as regex
import typing

import discord


class AcceptanceCheck(object):
    """A general helper to check if a user is saying yes or no to a given proposal"""

    PROPOSAL_YES = regex.compile(r"(?:i do)|(?:yes)|(?:of course)|(?:definitely)|(?:absolutely)|(?:yeah)|(?:yea)|(?:sure)|(?:accept)|(?:ya)", regex.IGNORECASE)
    PROPOSAL_NO = regex.compile(r"(?:i don't)|(?:i dont)|(?:no)|(?:to think)|(?:i'm sorry)|(?:im sorry)|(?:decline)|(?:nah)", regex.IGNORECASE)
    TIMEOUT = asyncio.TimeoutError
    __slots__ = ('target_id', 'channel_id', 'response')

    def __init__(self, target:typing.Union[discord.User, int], channel:typing.Union[discord.User, int]=None):
        self.target_id = getattr(target, 'id', target)
        self.channel_id = getattr(channel, 'id', channel)
        self.response = None

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
            self.response = 'NO' if no_regex else 'YES' # Both of these are truthy
        return self.response

    async def wait_for_response(self, bot):
        """Runs all the fancy bot.wait_for stuff right here so I can just reuse it elsewhere"""

        try:
            if bot.get_user(self.target_id).bot:
                self.response = 'YES'
            await bot.wait_for('message', check=self.check, timeout=60.0)
        except self.TIMEOUT as e:
            raise e
        return self.response
