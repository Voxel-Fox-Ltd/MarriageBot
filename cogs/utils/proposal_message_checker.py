import asyncio
import re

import aioredlock
import discord
from discord.ext import commands
import voxelbotutils as utils


def only_mention(user:discord.User) -> discord.AllowedMentions:
    return discord.AllowedMentions(users=[user])


def escape_markdown(value:str) -> str:
    return re.sub(r"([\*`_])", r"\\\g<1>", value)


class TickPayloadCheckResult(object):

    BOOLEAN_EMOJIS = {
        "TICK": ("<:tick_filled_yes:784976310366634034>", "\N{HEAVY CHECK MARK}",),
        "CROSS": ("<:tick_filled_no:784976328231223306>", "\N{HEAVY MULTIPLICATION X}",),
    }

    def __init__(self, ctx, emoji):
        self.ctx = ctx
        self.emoji = emoji

    @classmethod
    def from_payload(cls, payload):
        return cls(payload, str(payload.button.emoji))

    @property
    def is_tick(self):
        return self.emoji in self.BOOLEAN_EMOJIS["TICK"]

    def __bool__(self):
        valid_emojis = []
        for i in self.BOOLEAN_EMOJIS.values():
            valid_emojis.extend(i)
        return self.emoji in valid_emojis


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
        try:
            for i in user_ids:
                locks.append(await redis.lock_manager.lock(str(i), lock_timeout=120))
        except aioredlock.LockError:
            for i in locks:
                await redis.lock_manager.unlock(i)
            await redis.disconnect()
            raise ProposalInProgress()
        return cls(redis, *locks)

    async def unlock(self, *, disconnect_redis:bool=True):
        for i in self.locks:
            try:
                await self.redis.lock_manager.unlock(i)
            except aioredlock.LockError:
                pass
        if disconnect_redis:
            await self.redis.disconnect()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        await self.unlock()


async def send_proposal_message(
        ctx, user:discord.Member, text:str, *, timeout_message:str=None, cancel_message:str=None,
        allow_bots:bool=False) -> TickPayloadCheckResult:
    """
    Send a proposal message out to the user to see if they want to say yes or no.

    Args:
        ctx (utils.Context): The context object for the called command.
        user (discord.Member): The user who the calling user wants to ask out.
        text (str): The text to be sent when the user's proposal is started.

    Returns:
        TickPayloadCheckResult: The resulting reaction that either the user or the author gave.
    """

    timeout_message = timeout_message or f"Sorry, {ctx.author.mention}; your request to {user.mention} timed out - they didn't respond in time :<"
    cancel_message = cancel_message or f"Alright, {ctx.author.mention}; your request to {user.mention} has been cancelled."

    # Reply yes if we allow bots
    if allow_bots and user.bot:
        return TickPayloadCheckResult(ctx, TickPayloadCheckResult.BOOLEAN_EMOJIS["TICK"][0])

    # See if they want to say yes
    components = utils.ActionRow(
        utils.Button(
            "Yes",
            emoji=TickPayloadCheckResult.BOOLEAN_EMOJIS["TICK"][0],
            style=utils.ButtonStyle.SUCCESS,
        ),
        utils.Button(
            "No",
            emoji=TickPayloadCheckResult.BOOLEAN_EMOJIS["CROSS"][0],
            style=utils.ButtonStyle.DANGER,
        ),
    )
    message = await ctx.send(text, components=components)  # f"Hey, {user.mention}, do you want to adopt {ctx.author.mention}?"
    try:
        def check(p):
            if p.message.id != message.id:
                return False
            if p.user.id not in [user.id, ctx.author.id]:
                return False
            result = TickPayloadCheckResult.from_payload(p)
            if p.user.id == user.id:
                return result
            if p.user.id == ctx.author.id:
                return str(p.button.emoji) in result.BOOLEAN_EMOJIS["CROSS"]
            return False
        button_event = await ctx.bot.wait_for("button_click", check=check, timeout=60)
    except asyncio.TimeoutError:
        for button in components.components:
            button.disabled = True
        ctx.bot.loop.create_task(message.edit(components=components))
        await ctx.send(timeout_message, allowed_mentions=only_mention(ctx.author))
        return None

    # Check what they said
    for button in components.components:
        button.disabled = True
    ctx.bot.loop.create_task(message.edit(components=components))
    result = TickPayloadCheckResult.from_payload(button_event)
    if not result.is_tick:
        if button_event.user.id == ctx.author.id:
            await result.ctx.send(cancel_message, allowed_mentions=only_mention(ctx.author))
            return None
        await result.ctx.send(f"Sorry, {ctx.author.mention}; they said no :<")
        return None

    # Alright we done
    return result
