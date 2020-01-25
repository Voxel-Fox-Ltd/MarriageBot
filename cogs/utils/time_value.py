import re as regex
from datetime import datetime as dt, timedelta

from discord.ext import commands


class InvalidTimeDuration(commands.BadArgument):
    """A conversion error for time durations"""

    def __init__(self, value:str):
        self.value = value

    def __str__(self):
        return f"The value `{self.value}` could not be converted to a valid time duration."


class TimeValue(object):
    """An object that nicely converts an integer value into an easily readable string"""

    time_value_regex = regex.compile(r"^((\d+)d)?((\d+)h)?((\d+)m)?((\d+)s)?$")

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
    def get_quotient_and_remainder(value:int, divisor:int, raise_error_on_zero:bool=False):
        """Gets the quotiend AND remainder of a given value"""

        try:
            return value // divisor, value % divisor
        except ZeroDivisionError:
            return 0, value

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.clean} ({self.duration})>"

    @classmethod
    async def convert(cls, ctx:commands.Context, value:str) -> 'TimeValue':
        """Takes a value (1h/30m/10s/2d etc) and returns a TimeValue instance with the duration"""

        match = cls.time_value_regex.search(value)
        if match is None:
            raise InvalidTimeDuration(value)
        duration = 0

        """
        Group 2: days
        Group 4: hours
        Group 6: mins
        Group 8: seconds
        """

        if match.group(2):
            duration += int(match.group(2)) * 60 * 60 * 24
        if match.group(4):
            duration += int(match.group(4)) * 60 * 60
        if match.group(6):
            duration += int(match.group(6)) * 60
        if match.group(8):
            duration += int(match.group(8))
        return TimeValue(duration)
