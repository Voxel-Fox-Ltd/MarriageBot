import re

from datetime import datetime as dt


def fix_time_string(time_str: str):
    """
    Takes a string of Day/Month(/Year) and returns a tuple of (day, month, year/current year)
    """

    # Set up the Regex statement
    time_match = re.search(r"^(?P<day>\d+)\/(?P<month>\d+)(\/(?P<year>\d+))?$", time_str)

    # Set up the variables
    day = int(time_match.group("day"))
    month = int(time_match.group("month"))
    year = int(time_match.group("year") or dt.utcnow().year)

    return dt(year, month, day)
