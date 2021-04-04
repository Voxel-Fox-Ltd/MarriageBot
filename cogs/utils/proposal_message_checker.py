import asyncio
import re

import discord
from discord.ext import commands


def only_mention(user:discord.User) -> discord.AllowedMentions:
    return discord.AllowedMentions(users=[user])


def escape_markdown(value:str) -> str:
    return re.sub(r"([\*`_])", r"\\\g<1>", value)


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


class ProposalInProgress(commands.CommandError):
    """Raised when a user is currently in a proposal."""


class ProposalLock(object):

    def __init__(self, redis, *locks):
        self.redis = redis
        self.locks = locks

    @classmethod
    async def lock(cls, redis, *user_ids):
        locks = []
        if any([await redis.lock_manager.is_locked(str(i)) for i in user_ids]):
            raise ProposalInProgress()
        for i in user_ids:
            locks.append(await redis.lock_manager.lock(str(i)))
        return cls(redis, *locks)

    async def unlock(self, *, disconnect_redis:bool=True):
        for i in self.locks:
            await self.redis.lock_manager.unlock(i)
        if disconnect_redis:
            await self.redis.disconnect()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        await self.unlock()


async def send_proposal_message(
        ctx, user:discord.Member, text:str, *, timeout_message:str=None, cancel_message:str=None, allow_bots:bool=False) -> TickPayloadCheckResult:
    """
    Send a proposal message out to the user to see if they want to say yes or no.

    Args:
        ctx (utils.Context): The context object for the called command.
        user (discord.Member): The user who the calling user wants to ask out.
        text (str): The text to be sent when the user's proposal is started.

    Returns:
        TickPayloadCheckResult: The resulting reaction that either the user or the author gave.
    """

    timeout_message = timeout_message or f"Sorry, {ctx.author.mention}; your proposal to {user.mention} timed out - they didn't respond in time :<"
    cancel_message = cancel_message or f"Alright, {ctx.author.mention}; your proposal to {user.mention} has been cancelled."

    # Reply yes if we allow bots
    if allow_bots and user.bot:
        return TickPayloadCheckResult(TickPayloadCheckResult.BOOLEAN_EMOJIS["TICK"])

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
        await ctx.send(timeout_message, allowed_mentions=only_mention(ctx.author))
        return None

    # Check what they said
    result = TickPayloadCheckResult.from_payload(payload)
    if not result.is_tick:
        if payload.user_id == ctx.author.id:
            await ctx.send(cancel_message, allowed_mentions=only_mention(ctx.author))
            return None
        await ctx.send(f"Sorry, {ctx.author.mention}; they said no :<")
        return None

    # Alright we done
    return result
