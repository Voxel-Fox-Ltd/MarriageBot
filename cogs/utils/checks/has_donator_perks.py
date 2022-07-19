from discord.ext import commands, vbu

from cogs.utils.perks_handler import get_marriagebot_perks


__all__ = (
    'has_donator_perks',
)


def has_donator_perks(perk_name:str):
    async def predicate(ctx):
        perks = await get_marriagebot_perks(ctx.bot, ctx.author.id)
        v = getattr(perks, perk_name, False)
        if v:
            return v
        raise vbu.errors.IsNotUpgradeChatSubscriber()
    return commands.check(predicate)
