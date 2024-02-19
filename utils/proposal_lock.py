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
from typing import Callable

__all__ = (
    'ProposalLock',
    'PROPOSAL_TIMEOUT',
)


log = logging.getLogger("proposallock")


# PROPOSAL_TIMEOUT: float = 60.0
PROPOSAL_TIMEOUT: float = 5.0


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
                async def wrapper(l: asyncio.Lock):
                    await asyncio.sleep(timeout or 0)
                    try:
                        l.release()
                    except RuntimeError:
                        pass
                    except Exception as e:
                        log.error("Failed to release lock", exc_info=e)

                # Create timeout background task
                if timeout is not None:
                    t = asyncio.create_task(wrapper(lock))
                    cls._lock_timeouts[id] = t
                    def discard(i: int):
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
