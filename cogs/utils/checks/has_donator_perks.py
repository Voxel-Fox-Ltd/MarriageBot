from discord.ext import commands
import voxelbotutils as utils

from cogs.utils.perks_handler import get_marriagebot_perks


def has_donator_perks(perk_name:str):
    async def predicate(ctx):
    	bot_support = await utils.checks.is_bot_support().predicate(ctx)
    	if bot_support:
    		return True
    	else:
    		pass
        perks = await get_marriagebot_perks(ctx.bot, ctx.author.id)
        v = getattr(perks, perk_name, False)
        if v:
            return v
        raise utils.errors.IsNotUpgradeChatSubscriber()
    return commands.check(predicate)
