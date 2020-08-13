import discord
from discord.ext import commands


class IsNotDonator(commands.CheckFailure):
    """The base "not donator" error to join PayPal and Patreon"""

    pass


async def has_donator_perks_predicate(bot, desired_perk_name:str, user:discord.User):
    """Returns the max perk value for the given user based on their roles in the config
    as compared to the support guild
    """

    # Set the support guild if we have to
    if not bot.support_guild:
        await bot.fetch_support_guild()

    max_donator_perk_working = bot.config['role_perks']['default'].copy()

    # Get member and look for role
    try:
        member = await bot.support_guild.fetch_member(user.id)
        for role_id in member._roles:
            role_perks = bot.config['role_perks'].get(str(role_id))
            if role_perks is None:
                continue

            # Update the base dict with the better values
            for perk_name, perk_value in role_perks.items():
                if perk_value is True:
                    max_donator_perk_working[perk_name] = perk_value
                elif perk_name == 'max_children':
                    max_donator_perk_working[perk_name] = max([max_donator_perk_working[perk_name], perk_value])
                elif perk_name == 'tree_cooldown_time':
                    max_donator_perk_working[perk_name] = min([max_donator_perk_working[perk_name], perk_value])

    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        pass

    # Return the value we want to get
    if desired_perk_name not in max_donator_perk_working:
        raise commands.CommandError(f"The provided perk name {desired_perk_name} was not found in the perk dict")
    return max_donator_perk_working.get(desired_perk_name)


def has_donator_perks(desired_perk_name:str):
    """Gets the perk value for a given user"""

    async def predicate(ctx):
        v = await has_donator_perks_predicate(ctx.bot, desired_perk_name, ctx.author)
        if v is False:
            raise IsNotDonator()
        return v
    return commands.check(predicate)
