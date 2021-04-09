import typing
from datetime import datetime as dt, timedelta

import discord


class ProposalCache(dict):
    """A helper class to wrap around a dictionary so I can easily
    work out how to deal with what I'm given here instead of repeatedly
    in every cog

    Generally the setup of things here is self[user_id] = (ROLE, COG, TIMEOUT)
    """

    bot: "cogs.utils.custom_bot.CustomBot" = None

    def get(self, key, *args, d=None, ignore_timeout: bool = False, **kwargs):
        """Gets a key from self, as a normal dict would - but here we check
        if the timeout time has passed, in which case we return d

        Params:
            ignore_timeout: bool = False
                Whether we should ignore the timeout time and return the item anyway
        """

        # Get the item
        item = super().get(key, d, *args, **kwargs)

        # If it's nothing anyway
        if item in [None, d]:
            return item

        # If it's timed out
        if dt.now() > item[2] and ignore_timeout is False:
            return d

        # Return as normal
        return item

    async def add(
        self,
        instigator: typing.Union[int, discord.User],
        target: typing.Union[int, discord.User],
        cog: str,
    ):
        """Adds two users to the cache with the current time in tow

        Params:
            intigator
            target
                The two users who need to be cached
            cog: str
                The cog where the users need to be cached from
        """

        timeout_time = dt.now() + timedelta(seconds=60)
        async with self.bot.redis() as re:
            await re.publish_json(
                "ProposalCacheAdd",
                {
                    "instigator": getattr(instigator, "id", instigator),
                    "target": getattr(target, "id", target),
                    "cog": cog,
                    "timeout_time": timeout_time.isoformat(),
                },
            )
        self.raw_add(instigator, target, cog, timeout_time)

    def raw_add(
        self,
        instigator: typing.Union[int, discord.User],
        target: typing.Union[int, discord.User],
        cog: str,
        timeout_time: dt,
    ):
        """Adds a user to the cache without pinging the redis channel"""

        # Add to cache
        if isinstance(timeout_time, str):
            timeout_time = dt.strptime(
                timeout_time, "%Y-%m-%dT%H:%M:%S.%f"
            )  # Parse the time from string to DT
        self[getattr(instigator, "id", instigator)] = ("INSTIGATOR", cog, timeout_time)
        self[getattr(target, "id", target)] = ("TARGET", cog, timeout_time)

    async def remove(self, *elements) -> list:
        """Removes some given elements (proably discord.Users or IDs) via redis"""

        async with self.bot.redis() as re:
            await re.publish_json(
                "ProposalCacheRemove", [getattr(i, "id", i) for i in elements]
            )
        return self.raw_remove(*elements)

    def raw_remove(self, *elements) -> list:
        """Pops some elements from the cache"""

        for i in elements:
            try:
                self.pop(getattr(i, "id", i))
            except KeyError:
                pass
