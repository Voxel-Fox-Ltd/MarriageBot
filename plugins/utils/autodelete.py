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
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import novus as n

__all__ = (
    'AutoDelete',
)


class AutoDelete:
    """
    Handle message autodeleting.
    """

    PENDING_TASKS: dict[int, asyncio.Task] = {}
    PENDING_USERS: set[int] = set()

    @classmethod
    def autodelete(cls, message: n.Message, time_: float, **kwargs):
        """
        Set up a message to autodelete or auto-edit after a certain amount
        of time.
        """

        async def wrapper():
            timer = time_ - time.time()
            try:
                await asyncio.sleep(timer)
            except asyncio.CancelledError:
                return
            try:
                if kwargs:
                    await message.edit(**kwargs)
                else:
                    await message.delete()
            except Exception:
                pass

        t = asyncio.create_task(wrapper())
        cls.PENDING_TASKS[message.id] = t
        t.add_done_callback(lambda _: cls.PENDING_TASKS.pop(message.id, None))

    @classmethod
    def cancel(cls, message: n.Message):
        """
        Cancel a message delete task.
        """

        t = cls.PENDING_TASKS.pop(message.id, None)
        if t is None:
            return
        t.cancel()
