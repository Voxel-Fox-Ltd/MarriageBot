from __future__ import annotations

import asyncio
import re
from typing import Tuple, Union, Optional
import uuid

import aioredlock
import discord
from discord.ext import commands, vbu


MISSING = discord.utils.MISSING
only_mention = discord.AllowedMentions.only
vbu.Redis.lock_manager = aioredlock.Aioredlock([vbu.Redis.pool])


__all__ = (
    'escape_markdown',
    'TickPayloadCheckResult',
    'ProposalInProgress',
    'ProposalLock',
    'send_proposal_message',
)


def escape_markdown(value: str) -> str:
    """
    Escape Discord markdown.

    Parameters
    ----------
    value : str
        The string that you want to escape.

    Returns
    -------
    str
        The escaped string.
    """

    return re.sub(r"([\*`_])", r"\\\g<1>", value)


class TickPayloadCheckResult:
    """
    A comparible object for the proposal lock to manage.
    """

    def __init__(
            self,
            ctx: Union[commands.Context, discord.Interaction],
            response: str):
        self.ctx: Union[commands.Context, discord.Interaction] = ctx
        self.response: str = response

    @property
    def messageable(self) -> Union[discord.abc.Messageable, discord.Webhook]:
        if isinstance(self.ctx, discord.Interaction):
            return self.ctx.followup
        return self.ctx

    @classmethod
    def from_payload(cls, payload: discord.Interaction[str]):
        return cls(payload, payload.custom_id)

    @property
    def is_tick(self) -> bool:
        return self.response.endswith("YES")


class ProposalInProgress(commands.CommandError):
    """
    Raised when a user is currently in a proposal.
    """


class ProposalLock(object):

    def __init__(
            self,
            redis: vbu.Redis,
            *locks: str):
        self.redis: vbu.Redis = redis
        self.locks: Tuple[str] = locks

    @classmethod
    async def lock(
            cls,
            redis: vbu.Redis,
            *user_ids: int) -> ProposalLock:
        """
        Lock the given user IDs via redis.

        Parameters
        ----------
        redis : vbu.Redis
            An open redis instance.
        *user_ids : int
            A list of user IDs.

        Returns
        -------
        ProposalLock
            A lock instance for the given user IDs.

        Raises
        ------
        ProposalInProgress
            One or more of the users is already locked.
        """

        locks = []

        # See if any of them are locked already
        if any([await redis.lock_manager.is_locked(str(i)) for i in user_ids]):
            raise ProposalInProgress()

        # Try and lock the user IDs
        try:
            for i in user_ids:
                lock = await redis.lock_manager.lock(
                    str(i),
                    lock_timeout=120,
                )
                locks.append(lock)

        # Somehow one got locked between then and now
        except aioredlock.LockError:
            for i in locks:
                await redis.lock_manager.unlock(i)
            raise ProposalInProgress()

        # And return a new instance
        return cls(redis, *locks)

    async def unlock(
            self,
            *,
            disconnect_redis: bool = True):
        """
        Unlock all of the user IDs associated with this instance.

        Parameters
        ----------
        disconnect_redis : bool, optional
            Whether or not to disconnect the redis instance when we're
            finished unlocking.
        """

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


async def catch_edit(
        message: discord.Message,
        **kwargs) -> None:
    """
    Edit a message with the given kwargs and catch and discard
    any 4xxs.

    Parameters
    ----------
    message : discord.Message
        The message that you want to edit.
    **kwargs
        The kwargs and values that you want to edit.
    """

    try:
        await message.edit(**kwargs)
    except (discord.NotFound, discord.HTTPException):
        pass


async def send_proposal_message(
        ctx,
        user: Union[discord.Member, discord.User],
        text: str,
        *,
        timeout_message: str = MISSING,
        cancel_message: str = MISSING,
        allow_bots: bool = False) -> Optional[TickPayloadCheckResult]:
    """
    Send a proposal message out to the user to see if they want to say yes or no.

    Parameters
    ----------
    ctx : vbu.Context
        The context object for the called command.
    user : Union[discord.Member, discord.User]
        The user who the calling user wants to ask out.
    text : str
        The text to be sent when the user's proposal is started.
    timeout_message : str, optional
        An message to send if the wait_for times out.
    cancel_message : str, optional
        An override message to send if the user canceld their proposal.
    allow_bots : bool, optional
        Whether or not bots are allowed to say yes.

    Returns
    -------
    Optional[TickPayloadCheckResult]
        The resulting reaction that either the user or the author gave.
    """

    timeout_message = timeout_message or (
        f"Sorry, {ctx.author.mention}; your request to {user.mention} "
        "timed out - they didn't respond in time :<"
    )
    cancel_message = cancel_message or (
        f"Alright, {ctx.author.mention}; your request to {user.mention} "
        "has been cancelled."
    )

    # Reply yes if we allow bots
    if allow_bots and user.bot:
        return TickPayloadCheckResult(ctx, "YES")

    # Send some buttons
    component_id = str(uuid.uuid4())
    components = discord.ui.MessageComponents.boolean_buttons(
        yes=("Yes", f"{component_id} YES",),
        no=("No", f"{component_id} NO",),
    )
    message = await vbu.embeddify(ctx, text, components=components)

    # Set up a check
    def check(payload: discord.Interaction[str]):

        # See if it's relevant
        if not payload.custom_id.startswith(component_id):
            return
        assert payload.user

        # See if the user is an owner
        if payload.user.id in ctx.bot.owner_ids:
            return True

        # See if this user is valid
        if payload.user.id not in [user.id, ctx.author.id]:
            ctx.bot.loop.create_task(payload.response.send_message(
                "You can't respond to this proposal!",
                ephemeral=True,
            ))
            return False

        # If they're the target user they can click anything
        if payload.user.id == user.id:
            return True

        # If they're the send user they can only click no
        if payload.user.id == ctx.author.id:
            if payload.custom_id.endswith("YES"):
                ctx.bot.loop.create_task(payload.response.send_message(
                    "You can't accept your own proposal!",
                    ephemeral=True,
                ))
                return False

        # Ay fallback, they can
        return True

    # Wait for a response
    try:
        button_event: discord.Interaction[str] = await ctx.bot.wait_for(
            "component_interaction",
            check=check,
            timeout=60,
        )
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
            await vbu.embeddify(
                result.ctx.followup,  # type: ignore
                cancel_message,
                allowed_mentions=only_mention(ctx.author),
            )
            return None
        await vbu.embeddify(
            result.ctx.followup,  # type: ignore
            f"Sorry, {ctx.author.mention}; they said no :<",
        )
        return None

    # Alright we done
    return result
