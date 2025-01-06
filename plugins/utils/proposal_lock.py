"""
Copyright (c) Kae Bartlett

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""

from __future__ import annotations

import asyncio
import collections
import functools
import logging
import time
from typing import TYPE_CHECKING, Callable, Literal

import novus as n

from .autodelete import AutoDelete
from .family_member import FamilyMember
from .perks import Perks
from .utils import e, get_guild_id

if TYPE_CHECKING:
    from novus import types as t
    from novus.ext import client

__all__ = (
    'ProposalLock',
    'PROPOSAL_TIMEOUT',
    'handle_proposal',
)


log = logging.getLogger("proposallock")


PROPOSAL_TIMEOUT: float = 60.0
# PROPOSAL_TIMEOUT: float = 10.0


async def handle_proposal(
        bot: client.Client,
        ctx: t.CommandGI,
        user: n.GuildMember,
        message: str,
        button_action: Literal["MARRY", "ADOPT", "MAKEPARENT"]) -> bool:
    """
    Handle blacklisted users, bots, and all that malarkey.
    """

    # Check they're not the same user
    if ctx.user == user:
        await ctx.send(
            ctx._("You can't run this on yourself :/"),
            ephemeral=True
        )
        return False

    # Check against bots
    if user.bot:
        await ctx.send(
            ctx._("You can't run this on bots :/"),
            ephemeral=True
        )
        return False

    # Check if either user is currently waiting on a proposal
    if (status := ProposalLock.locked(ctx.user.id, user.id)) >= 0:
        if status == 0:
            await ctx.send(
                ctx._("You're already waiting on a proposal."),
                ephemeral=True,
            )
        elif status == 1:
            await ctx.send(
                (
                    ctx._("{user} is already waiting on a proposal.")
                    .format(user=user.mention)
                ),
                ephemeral=True,
            )
        else:
            raise Exception("Invalid lock state")
        return False

    # Lock the users so they can't be proposed to
    unlock_f = await ProposalLock.lock(ctx.user.id, user.id)
    if unlock_f is None:
        return False  # Failed to lock

    # Show the users a loading screen
    await ctx.defer()

    # Get the users so we can run relevant checks
    guild_id: int = get_guild_id(bot, ctx)
    author_ft, user_ft = FamilyMember.get_multiple(ctx.user.id, user.id, guild_id=guild_id)

    # Work out which checks we need to perform
    if button_action == "MARRY":
        author_perks = await Perks.get_perks_for_user(bot, ctx.user.id)
        if (num := len(author_ft._partner_ids)) >= author_perks.max_partners:
            unlock_f()
            await ctx.send(
                ctx._(
                    (
                        "You already have {partner_count} partners! "
                        "You can't have any more right now :<"
                    )
                ).format(partner_count=num)  # TODO upsell
            )
            return False
        user_perks = await Perks.get_perks_for_user(bot, user.id)
        if (num := len(user_ft._partner_ids)) >= user_perks.max_partners:
            unlock_f()
            await ctx.send(
                ctx._(
                    (
                        "{user} already has {partner_count} partners! "
                        "They can't have any more right now :<"
                    )
                ).format(user=f"<@{user.id}>", partner_count=num),
                allowed_mentions=n.AllowedMentions.none(),
            )
            return False
    elif button_action == "ADOPT":
        if user_ft._parent_id is not None:
            unlock_f()
            await ctx.send(
                (
                    ctx._("{user} already has a parent! They can only have one!")
                    .format(user=f"<@{user.id}>")
                ),
                allowed_mentions=n.AllowedMentions.none(),
            )
            return False
        author_perks = await Perks.get_perks_for_user(bot, ctx.user.id)
        if (num := len(author_ft._child_ids)) >= author_perks.max_children:
            unlock_f()
            await ctx.send(
                ctx._(
                    (
                        "You already have {child_count} children! "
                        "You can't have any more right now :<"
                    )
                ).format(child_count=num),  # TODO upsell
                allowed_mentions=n.AllowedMentions.none(),
            )
            return False
    elif button_action == "MAKEPARENT":
        if author_ft._parent_id is not None:
            unlock_f()
            await ctx.send(
                ctx._("You already have a parent! You can only have one!"),
            )
            return False
        user_perks = await Perks.get_perks_for_user(bot, user.id)
        if (num := len(user_ft._child_ids)) >= user_perks.max_children:
            unlock_f()
            await ctx.send(
                ctx._(
                    (
                        "{user} already has {child_count} children! "
                        "They can't have any more right now :<"
                    )
                ).format(user=f"<@{user.id}>", child_count=num),
                allowed_mentions=n.AllowedMentions.none(),
            )
            return False

    # See if they're already related
    if await author_ft.get_related(user_ft):
        unlock_f()
        await ctx.send(
            embeds=e(
                ctx._("You and {user} are already related!")
                .format(user=user.mention)
            ),
            allowed_mentions=n.AllowedMentions.none(),
        )
        return False

    # See if they're above a certain family size limit
    family_size_limit: int = 2_000
    kwargs = {
        "people_list": None,
        "add_parent": True,
        "add_partners": True,
        "add_partner_parents": True,
    }

    async def chained():
        async for i in author_ft.span(**kwargs):
            yield i
        async for i in user_ft.span(**kwargs):
            yield i

    counter: int = 0
    async for counter, _ in chained():
        if counter > family_size_limit:
            unlock_f()
            await ctx.send(
                embeds=e(
                    ctx._(
                        "You can't do that! If your families combine, you'd "
                        "have over {family_size} members in your tree!"
                    )
                    .format(family_size=family_size_limit)
                )
            )
            return False
        counter += 1

    # Send the actual proposal message
    time_ = int(time.time() + PROPOSAL_TIMEOUT)
    m = await ctx.followup(
        embeds=e(message.format(user=user.mention, author=ctx.user.mention)),
        components=[
            n.ActionRow([
                n.Button(
                    # TRANSLATORS: Label on a button
                    ctx._("Yes"),
                    style=n.ButtonStyle.GREEN,
                    custom_id=f"PROPOSE {button_action} 1 {ctx.user.id} {user.id} {time_}",
                ),
                n.Button(
                    # TRANSLATORS: Label on a button
                    ctx._("No"),
                    style=n.ButtonStyle.RED,
                    custom_id=f"PROPOSE {button_action} 0 {ctx.user.id} {user.id} {time_}",
                ),
            ]),
        ],
    )
    AutoDelete.autodelete(
        m, time_,
        content=None,
        embeds=e(
            ctx._("Sorry, {author}, your proposal to {user} has timed out!")
            .format(author=ctx.user.mention, user=user.mention)
        ),
        components=None,
    )
    return True


class ProposalLock:

    PROPOSAL_LOCKS: dict[int, asyncio.Lock] = collections.defaultdict(asyncio.Lock)
    _lock_timeouts: dict[int, asyncio.Task] = {}

    @classmethod
    def locked(cls, *ids: int) -> int:
        """
        Check if a range of IDs are proposal locked. Returns the index of the
        locked lock, or ``-1``.
        """

        for idx, id in enumerate(ids):
            lock = cls.PROPOSAL_LOCKS[id]
            if lock.locked():
                return idx
        return -1

    @classmethod
    async def lock(
            cls,
            *ids: int,
            timeout: float | None = PROPOSAL_TIMEOUT) -> Callable[[], None] | None:
        """
        Place an asyncio lock on a range of IDs.
        """

        created: list[int] = []

        # For each given ID
        for id in ids:

            # Try/catch for getting stuck on a lock acquire
            try:

                # Get and lock the lock
                lock = cls.PROPOSAL_LOCKS[id]
                await asyncio.wait_for(lock.acquire(), timeout=0.2)

                # Add to created set so we can reference in the case of a
                # failure
                created.append(id)

                # Anonymous function for use with timeout
                async def wrapper(lock_: asyncio.Lock) -> None:
                    await asyncio.sleep(timeout or 0)
                    try:
                        lock_.release()
                    except RuntimeError:
                        pass
                    except Exception as e_:
                        log.error("Failed to release lock", exc_info=e_)

                # Create timeout background task
                if timeout is not None:
                    t = asyncio.create_task(wrapper(lock))
                    cls._lock_timeouts[id] = t

                    def discard(i: int) -> None:
                        cls._lock_timeouts.pop(i, None)
                        cls.PROPOSAL_LOCKS.pop(i, None)
                    t.add_done_callback(lambda _: discard(id))

            # On failure to acquire lock, unlock anything successfully created
            except asyncio.TimeoutError as e:
                log.error("Failed to lock", exc_info=e)
                cls.unlock(*created)
                return None

        return functools.partial(cls.unlock, *ids)

    @classmethod
    def unlock(cls, *ids: int) -> None:
        """
        Unlock a currently locked lock, silently discarding any errors.
        """

        for id in ids:

            # Release
            lock = cls.PROPOSAL_LOCKS[id]
            try:
                lock.release()
            except RuntimeError:
                pass

            # Cancel release timeout background task
            try:
                t = cls._lock_timeouts.pop(id, None)
                if t is not None:
                    t.cancel()
            except Exception:
                pass
