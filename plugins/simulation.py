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

import novus as n
from novus import types as t
from novus.ext import client
from novus.utils import Localization as LC


class Simulation(client.Plugin):

    @client.command(name="kiss")
    async def kiss(self, ctx: t.CommandI) -> None:
        ...

    @client.command(name="hug")
    async def hug(self, ctx: t.CommandI) -> None:
        ...

    @client.command(name="stab")
    async def stab(self, ctx: t.CommandI) -> None:
        ...

    @client.command(name="punch")
    async def punch(self, ctx: t.CommandI) -> None:
        ...

    @client.command(name="bite")
    async def bite(self, ctx: t.CommandI) -> None:
        ...

    @client.command(name="slap")
    async def slap(self, ctx: t.CommandI) -> None:
        ...

