from discord.ext import commands, vbu

from cogs.utils.perks_handler import get_marriagebot_perks


__all__ = (
    'has_donator_perks',
)


class IsNotSubscriber(commands.CheckFailure):
    """The error raised when the user is missing a subscription."""

    def __init__(self):
        super().__init__(
            (
                "You need to be subscribed to the bot to run this command - "
                "see `/info` for more information."
            )
        )


def has_donator_perks(perk_name:str):
    async def predicate(ctx):
        perks = await get_marriagebot_perks(ctx.bot, ctx.author.id)
        v = getattr(perks, perk_name, False)
        if v:
            return v
        raise IsNotSubscriber()
    return commands.check(predicate)
