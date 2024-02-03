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
from novus.utils import Localization as LC
from novus.ext import client


class Marriage(client.Plugin):

    @client.command(name="marry")
    async def marry(self, ctx: t.CommandI) -> None:
        ...

    @client.command(name="divorce")
    async def divorce(self, ctx: t.CommandI) -> None:
        ...

