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


class Information(client.Plugin):

    @client.command(name="children")
    async def children(self, ctx: t.CommandI) -> None:
        ...

    @client.command(name="partners")
    async def partners(self, ctx: t.CommandI) -> None:
        ...

    @client.command(name="parent")
    async def parent(self, ctx: t.CommandI) -> None:
        ...

    @client.command(name="familysize")
    async def familysize(self, ctx: t.CommandI) -> None:
        ...

    @client.command(name="tree")
    async def tree(self, ctx: t.CommandI) -> None:
        ...

    @client.command(name="bloodtree")
    async def bloodtree(self, ctx: t.CommandI) -> None:
        ...

