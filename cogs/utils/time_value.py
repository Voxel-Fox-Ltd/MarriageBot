import re as regex
from datetime import timedelta

from discord.ext import commands


class InvalidTimeDuration(commands.BadArgument):
    """A conversion error for time durations"""

    def __init__(self, value:str):
        self.value = value

    def __str__(self):
        return f"The value `{self.value}` could not be converted to a valid time duration."


class TimeValue(object):
    """An object that nicely converts an integer value into an easily readable string"""

    time_value_regex = regex.compile(r"^(?:(?P<days>\d+)d)?(?:(?P<hours>\d+)h)?(?:(?P<minutes>\d+)m)?(?:(?P<seconds>\d+)s)?$")

    def __init__(self, duration:int):
        self.duration = int(duration)
        days, remaining = self.get_quotient_and_remainder(self.duration, 60 * 60 * 24)
        hours, remaining = self.get_quotient_and_remainder(remaining, 60 * 60)
        minutes, remaining = self.get_quotient_and_remainder(remaining, 60)
        seconds = remaining
        self.clean_spaced = f"{str(days) + 'd ' if days > 0 else ''}{str(hours) + 'h ' if hours > 0 else ''}{str(minutes) + 'm ' if minutes > 0 else ''}{str(seconds) + 's ' if seconds > 0 else ''}".strip()
        self.clean = self.clean_spaced.replace(" ", "")
        self.delta = timedelta(seconds=self.duration)

    @staticmethod
    def get_quotient_and_remainder(value:int, divisor:int):
        """Gets the quotiend AND remainder of a given value"""

        try:
            return value // divisor, value % divisor
        except ZeroDivisionError:
            return 0, value

    def __str__(self):
        return self.clean

    def __repr__(self):
        return f"{self.__class__.name__}.parse('{self.clean}')"

    @classmethod
    async def convert(cls, ctx:commands.Context, value:str) -> 'TimeValue':
        """Takes a value (1h/30m/10s/2d etc) and returns a TimeValue instance with the duration"""

        return cls.parse(value)

    @classmethod
    def parse(cls, value:str) -> 'TimeValue':
        """Takes a value (1h/30m/10s/2d etc) and returns a TimeValue instance with the duration"""

        match = cls.time_value_regex.search(value)
        if match is None:
            raise InvalidTimeDuration(value)
        duration = 0

        if match.group('days'):
            duration += int(match.group('days')) * 60 * 60 * 24
        if match.group('hours'):
            duration += int(match.group('hours')) * 60 * 60
        if match.group('minutes'):
            duration += int(match.group('minutes')) * 60
        if match.group('seconds'):
            duration += int(match.group('seconds'))
        return cls(duration)
