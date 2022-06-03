import asyncio
import re
import typing

import aioredlock
import discord
from discord.ext import commands, vbu


def only_mention(user: typing.Union[discord.Member, discord.User]) -> discord.AllowedMentions:
    return discord.AllowedMentions(users=[user])


def escape_markdown(value: str) -> str:
    return re.sub(r"([\*`_])", r"\\\g<1>", value)


class TickPayloadCheckResult(object):

    def __init__(self, ctx, response):
        self.ctx: typing.Union[commands.Context, discord.Interaction] = ctx
        self.response = response

    @property
    def messageable(self) -> discord.abc.Messageable:
        if isinstance(self.ctx, discord.Interaction):
            return self.ctx.followup
        return self.ctx

    @classmethod
    def from_payload(cls, payload):
        return cls(payload, payload.component.custom_id)

    @property
    def is_tick(self):
        return self.response == "YES"

    def __bool__(self):
        return True


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

    async def unlock(self, *, disconnect_redis: bool = True):
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


async def catch_edit(message: discord.Message, **kwargs) -> None:
    """
    Edit a message with the given kwargs and catch and discard any 404s.
    """

    try:
        await message.edit(**kwargs)
    except (discord.NotFound, discord.HTTPException):
        pass


async def send_proposal_message(
        ctx, user: typing.Union[discord.Member, discord.User], text: str, *, timeout_message: str = None,
        cancel_message: str = None, allow_bots: bool = False) -> typing.Optional[TickPayloadCheckResult]:
    """
    Send a proposal message out to the user to see if they want to say yes or no.

    Args:
        ctx (vbu.Context): The context object for the called command.
        user (discord.Member): The user who the calling user wants to ask out.
        text (str): The text to be sent when the user's proposal is started.

    Returns:
        TickPayloadCheckResult: The resulting reaction that either the user or the author gave.
    """

    timeout_message = timeout_message or f"Sorry, {ctx.author.mention}; your request to {user.mention} timed out - they didn't respond in time :<"
    cancel_message = cancel_message or f"Alright, {ctx.author.mention}; your request to {user.mention} has been cancelled."

    # Reply yes if we allow bots
    if allow_bots and user.bot:
        return TickPayloadCheckResult(ctx, "YES")

    # Send some buttons
    components = discord.ui.MessageComponents.boolean_buttons(
        yes=("Yes", "YES",),
        no=("No", "NO",),
    )
    message = await vbu.embeddify(ctx, text, components=components)  # f"Hey, {user.mention}, do you want to adopt {ctx.author.mention}?"

    # Set up a check
    def check(payload: discord.Interaction):
        assert payload.message
        assert payload.user
        assert payload.component
        if payload.message.id != message.id:
            return False  # not relevant to this request
        if payload.user.id not in [user.id, ctx.author.id]:
            ctx.bot.loop.create_task(payload.response.send_message("You can't respond to this proposal!", ephemeral=True))
            return False  # user isn't whitelisted
        if payload.user.id == user.id:
            return True
        if payload.user.id == ctx.author.id:
            if payload.custom_id != "NO":
                ctx.bot.loop.create_task(payload.response.send_message("You can't accept your own proposal!", ephemeral=True))
                return False
        return True

    # Wait for a response
    try:
        button_event: discord.Interaction = await ctx.bot.wait_for("component_interaction", check=check, timeout=60)
        assert button_event.user
        await button_event.response.defer()
    except asyncio.TimeoutError:
        ctx.bot.loop.create_task(catch_edit(message, components=components.disable_components()))
        await ctx.send(timeout_message, allowed_mentions=only_mention(ctx.author))
        return None

    # Check what they said
    ctx.bot.loop.create_task(catch_edit(message, components=components.disable_components()))
    result = TickPayloadCheckResult.from_payload(button_event)
    if not result.is_tick:
        if button_event.user.id == ctx.author.id:
            await vbu.embeddify(result.ctx.followup, cancel_message, allowed_mentions=only_mention(ctx.author))
            return None
        await vbu.embeddify(result.ctx.followup, f"Sorry, {ctx.author.mention}; they said no :<")
        return None

    # Alright we done
    return result
