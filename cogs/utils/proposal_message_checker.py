import asyncio

import discord


def only_mention(user:discord.User) -> discord.AllowedMentions:
    return discord.AllowedMentions(users=[user])


class TickPayloadCheckResult(object):

    # BOOLEAN_EMOJIS = ["\N{HEAVY CHECK MARK}", "\N{HEAVY MULTIPLICATION X}"]
    BOOLEAN_EMOJIS = {
        "TICK": "<:tick_filled_yes:784976310366634034>",
        "CROSS": "<:tick_filled_no:784976328231223306>",
    }

    def __init__(self, emoji):
        self.emoji = emoji

    @classmethod
    async def add_tick_emojis(cls, message):
        for emoji in cls.BOOLEAN_EMOJIS.values():
            await message.add_reaction(emoji)

    @classmethod
    def add_tick_emojis_non_async(cls, message):
        return asyncio.Task(cls.add_tick_emojis(message))

    @classmethod
    def from_payload(cls, payload):
        return cls(str(payload.emoji))

    @property
    def is_tick(self):
        return self.emoji == self.BOOLEAN_EMOJIS["TICK"]

    def __bool__(self):
        return self.emoji in self.BOOLEAN_EMOJIS.values()


async def send_proposal_message(ctx, user:discord.Member, text:str) -> TickPayloadCheckResult:
    """
    Send a proposal message out to the user to see if they want to say yes or no.

    Args:
        ctx (utils.Context): The context object for the called command.
        user (discord.Member): The user who the calling user wants to ask out.
        text (str): The text to be sent when the user's proposal is started.

    Returns:
        TickPayloadCheckResult: The resulting reaction that either the user or the author gave.
    """

    # See if they want to say yes
    message = await ctx.send(text)  # f"Hey, {user.mention}, do you want to adopt {ctx.author.mention}?"
    TickPayloadCheckResult.add_tick_emojis_non_async(message)
    try:
        def check(p):
            if p.message_id != message.id:
                return False
            if p.user_id not in [user.id, ctx.author.id]:
                return False
            result = TickPayloadCheckResult.from_payload(p)
            if p.user_id == user.id:
                return result
            if p.user_id == ctx.author.id:
                return str(p.emoji) == result.BOOLEAN_EMOJIS["CROSS"]
            return False
        payload = await ctx.bot.wait_for("raw_reaction_add", check=check, timeout=60)
    except asyncio.TimeoutError:
        await ctx.send(
            f"Sorry, {ctx.author.mention}; your proposal to {user.mention} timed out - they didn't respond in time :<",
            allowed_mentions=only_mention(ctx.author)
        )
        return None

    # Check what they said
    result = TickPayloadCheckResult.from_payload(payload)
    if not result.is_tick:
        if payload.user_id == ctx.author.id:
            await ctx.send(
                f"Alright, {ctx.author.mention}; your proposal to {user.mention} has been cancelled.",
                allowed_mentions=only_mention(ctx.author)
            )
            return None
        await ctx.send(f"Sorry, {ctx.author.mention}; they said no :<")
        return None

    # Alright we done
    return result
