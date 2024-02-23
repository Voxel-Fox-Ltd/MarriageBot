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

import collections
import itertools
import random
import string
from typing import TYPE_CHECKING, Any, Generator, TypeAlias, Union

import novus as n
from novus.ext import database as db
from typing_extensions import Self

if TYPE_CHECKING:
    import asyncpg

    from .custom_tree import CustomTree

    GuildID: TypeAlias = int
    UserID: TypeAlias = int

    AnyUser: TypeAlias = Union[
        int,
        n.GuildMember,
        n.User,
        "FamilyMember",
    ]

__all__ = (
    'FamilyMember',
)


def get_cluster_name(k: int = 5) -> str:
    return "".join([random.choice(string.ascii_uppercase) for _ in range(k)])


class FamilyMemberDB:

    __slots__ = ('f',)

    def __init__(self, f: FamilyMember):
        self.f = f

    async def add_parent(
            self,
            conn: asyncpg.Connection | asyncpg.Pool,
            user: FamilyMember) -> None:
        """
        Add a parent to the user via the database. Does the same for the other
        specified user, also affecting the cache.
        """

        await conn.execute(
            """
            INSERT INTO
                parents
                (child_id, parent_id, guild_id, timestamp)
            VALUES
                ($1, $2, $3, TIMEZONE('UTC', NOW()))
            """,
            self.f.id, user.id, self.f.guild_id,
        )
        self.f.add_parent(user)

    async def add_partner(
            self,
            conn: asyncpg.Connection | asyncpg.Pool,
            user: FamilyMember) -> None:
        """
        Add a partner to the user in the database. Does the same for the other
        specified user, also affecting the cache.
        """

        await conn.execute(
            """
            INSERT INTO
                marriages
                (user_id, partner_id, guild_id, timestamp)
            VALUES
                ($1, $2, $3, TIMEZONE('UTC', NOW()))
            ON CONFLICT
                (user_id, partner_id, guild_id)
            DO NOTHING
            """,
            *sorted([self.f.id, user.id]), self.f.guild_id,
        )
        self.f.add_partner(user)

    async def add_child(
            self,
            conn: asyncpg.Connection | asyncpg.Pool,
            user: FamilyMember) -> None:
        """
        Add a child to the user in the database. Does the same for the other
        specified user, also affecting the cache.
        """

        await conn.execute(
            """
            INSERT INTO
                parents
                (child_id, parent_id, guild_id, timestamp)
            VALUES
                ($1, $2, $3, TIMEZONE('UTC', NOW()))
            """,
            user.id, self.f.id, self.f.guild_id,
        )
        self.f.add_child(user)

    async def remove_parent(
            self,
            conn: asyncpg.Connection | asyncpg.Pool) -> None:
        """
        Remove a parent from the user in the database. Does the same for the
        current parent, also affecting the cache.
        """

        await conn.execute(
            """
            DELETE FROM
                parents
            WHERE
                child_id = $1
                AND guild_id = $3
            """,
            self.f.id, self.f.guild_id,
        )
        self.f.remove_parent()

    async def remove_partner(
            self,
            conn: asyncpg.Connection | asyncpg.Pool,
            user: FamilyMember) -> None:
        """
        Remove a partner from the user in the database. Does the same for the
        other specified user, also affecting the cache.
        """

        await conn.execute(
            """
            DELETE FROM
                marriages
            WHERE
                (
                    (
                        user_id = $1
                        AND partner_id = $2
                    )
                    OR (
                        user_id = $2
                        AND partner_id = $1
                    )
                )
                AND guild_id = $3
            """,
            self.f.id, user.id, self.f.guild_id,
        )
        self.f.remove_partner(user)

    async def remove_child(
            self,
            conn: asyncpg.Connection | asyncpg.Pool,
            user: FamilyMember) -> None:
        """
        Remove a child from the user in the database. Does the same or the
        other specified user, also affecting the cache.
        """

        await conn.execute(
            """
            DELETE FROM
                parents
            WHERE
                child_id = $1
                AND parent_id = $2
                AND guild_id = $3
            """,
            user.id, self.f.id, self.f.guild_id,
        )
        self.f.remove_child(user)


class FamilyMember:
    """
    An object representing a family member.
    """

    ALL_MEMBERS: dict[tuple[GuildID, UserID], Self] = {}

    __slots__ = (
        'id',
        'guild_id',
        '_parent_id',
        '_partner_ids',
        '_child_ids',
    )

    def __init__(
            self,
            id: int,
            guild_id: int = 0,
            parent: int | None = None,
            partners: list[int] | None = None,
            children: list[int] | None = None):
        self.id: int = id
        self.guild_id: int = guild_id
        self._parent_id: int | None = parent or None
        self._partner_ids: set[int] = set(partners or [])
        self._child_ids: set[int] = set(children or [])
        self.ALL_MEMBERS[(self.guild_id, self.id,)] = self

    @classmethod
    async def fetch_partners(
            cls,
            conn: asyncpg.Connection,
            user: AnyUser,
            guild_id: int = 0) -> list[tuple[int, n.utils.DiscordDatetime]]:
        """
        Fetch partners from the database.
        """

        user = cls._get_id(user)
        rows = await conn.fetch(
            """
            SELECT
                user_id,
                partner_id,
                timestamp
            FROM
                marriages
            WHERE
                (
                    user_id = $1
                    OR partner_id = $1
                )
                AND guild_id = $2
            """,
            user, guild_id,
        )
        ret = []
        for r in rows:
            u = r["user_id"]
            if u == user:
                u = r["partner_id"]
            ret.append((u, n.utils.DiscordDatetime.from_native(r["timestamp"]),))
        return ret

    @classmethod
    async def fetch_children(
            cls,
            conn: asyncpg.Connection,
            user: AnyUser,
            guild_id: int = 0) -> list[tuple[int, n.utils.DiscordDatetime]]:
        """
        Fetch children from the database.
        """

        user = cls._get_id(user)
        rows = await conn.fetch(
            """
            SELECT
                child_id,
                timestamp
            FROM
                parents
            WHERE
                parent_id = $1
                AND guild_id = $2
            """,
            user, guild_id,
        )
        return [
            (r["child_id"], n.utils.DiscordDatetime.from_native(r["timestamp"]),)
            for r in rows
        ]

    @classmethod
    async def fetch_parent(
            cls,
            conn: asyncpg.Connection,
            user: AnyUser,
            guild_id: int = 0) -> tuple[int, n.utils.DiscordDatetime] | None:
        """
        Fetch a parent from the database.
        """

        user = cls._get_id(user)
        rows = await conn.fetch(
            """
            SELECT
                parent_id,
                timestamp
            FROM
                parents
            WHERE
                child_id = $1
                AND guild_id = $2
            """,
            user, guild_id,
        )
        if not rows:
            return None
        return (rows[0]["child_id"], n.utils.DiscordDatetime.from_native(rows[0]["timestamp"]),)

    @staticmethod
    def _get_id(user: AnyUser) -> int:
        """
        Get the user ID from an anyuser instance.
        """

        if isinstance(user, int):
            pass
        else:
            user = user.id
        return user

    @classmethod
    def get(cls, user: AnyUser, guild_id: int = 0) -> Self:
        """
        Get a family member object from the cache.
        """

        user = cls._get_id(user)
        v = cls.ALL_MEMBERS.get((guild_id, user))
        if v is None:
            v = cls(user, guild_id)
        return v

    @classmethod
    def get_multiple(cls, *id: int, guild_id: int = 0) -> Generator[Self, None, None]:
        """
        Get multiple family members at once.
        """

        for i in id:
            yield cls.get(i, guild_id)

    @property
    def db(self) -> FamilyMemberDB:
        return FamilyMemberDB(self)

    @property
    def parent(self) -> Self | None:
        """
        Get the parent for this user from cache.
        """

        if self._parent_id:
            return self.get(self._parent_id, self.guild_id)
        return None

    @property
    def children(self) -> Generator[Self, None, None]:
        """
        Get the children for this user from cache.
        """

        for i in self._child_ids:
            yield self.get(i, self.guild_id)

    @property
    def partners(self) -> Generator[Self, None, None]:
        """
        Get the partners for this user from cache.
        """

        for i in self._partner_ids:
            yield self.get(i, self.guild_id)

    def add_child(self, user: AnyUser) -> FamilyMember:
        """
        Add a child to the current user, adding the current user to the
        child's parent as well.
        """

        user_object = self.get(user, self.guild_id)
        self._child_ids.add(user_object.id)
        user_object._parent_id = self.id
        return user_object

    def add_parent(self, user: AnyUser) -> FamilyMember:
        """
        Add a parent to the current user, adding the current user to the
        parent's children list as well.
        """

        parent_object = self.get(user, self.guild_id)
        self._parent_id = parent_object.id
        parent_object._child_ids.add(self.id)
        return parent_object

    def add_partner(self, user: AnyUser) -> FamilyMember:
        """
        Add a partner to the current user, adding the current user to the
        partner's partners as well.
        """

        partner_object = self.get(user, self.guild_id)
        self._partner_ids.add(partner_object.id)
        partner_object._partner_ids.add(self.id)
        return partner_object

    def remove_child(self, user: AnyUser) -> FamilyMember:
        """
        Remove a child from this user, removing this user from the child's
        parent attribute as well.
        """

        user_object = self.get(user, self.guild_id)
        try:
            self._child_ids.remove(user_object.id)
        except Exception:
            pass
        user_object._parent_id = None
        return user_object

    def remove_parent(self) -> FamilyMember | None:
        """
        Remove a parent from this user, removing this user from the parent's
        children as well.

        If this user does not have a parent, then ``None`` will be returned
        instead. This may prove to be an issue if this user is in another's
        child list.
        """

        user_object = self.parent
        if user_object is None:
            return None
        self._parent_id = None
        try:
            user_object._child_ids.remove(self.id)
        except Exception:
            pass
        return user_object

    def remove_partner(self, user: AnyUser) -> FamilyMember:
        """
        Remove a partner from this user, removing this user from the other
        user's partners as well.
        """

        user_object = self.get(user, self.guild_id)
        try:
            self._partner_ids.remove(user_object.id)
        except Exception:
            pass
        try:
            user_object._partner_ids.remove(self.id)
        except Exception:
            pass
        return user_object

    def __repr__(self) -> str:
        attrs = (
            ("id", "id",),
            ("children", "_child_ids",),
            ("parent_id", "_parent_id",),
            ("partners", "_partner_ids",),
            ("guild_id", "guild_id",),
        )
        d = ", ".join(["%s=%r" % (i, getattr(self, o)) for i, o in attrs])
        return f"{self.__class__.__name__}({d})"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return all([
            self.id == other.id,
            self.guild_id == other.guild_id,
        ])

    def __hash__(self) -> int:
        return hash(("FamilyMember", self.id, self.guild_id))

    @property
    def empty(self) -> bool:
        """
        Whether or not the current user has a family to put into a tree.
        """

        if self._child_ids:
            return True
        if self._partner_ids:
            return True
        if self._parent_id:
            return True
        return False

    def span(
            self,
            people_list: set[Self] | None = None,
            add_parent: bool = True,
            add_partners: bool = True,
            add_partner_parents: bool = False,
            generation: int = 0) -> Generator[tuple[int, Self], None, None]:
        """
        Get all users related to the current user, in no particular order.
        """

        # Set a default people list
        if people_list is None:
            people_list = set()

        # Return current user
        if self in people_list:
            return
        yield (generation, self,)
        people_list.add(self)

        # Return parent and their relations
        if add_parent:
            if self.parent:
                yield from self.parent.span(
                    people_list,
                    generation=generation - 1,
                )

        # Return children and their relations
        for child in self.children:
            yield from child.span(
                people_list,
                add_parent=False,
                generation=generation + 1,
            )

        # Return partner and their relations
        if add_partners:
            for partner in self.partners:
                yield from partner.span(
                    people_list,
                    add_parent=add_partner_parents,
                    add_partners=False,
                    generation=generation,
                )

    def get_related(self, other: Self) -> bool:
        """
        See if the current user is related to another.
        """

        for i in self.span(add_parent=True, add_partners=True, add_partner_parents=True):
            if i == other:
                return True
        return False

    def generation_span(self) -> Generator[set[Self], None, None]:
        """
        Get the relations for the current user grouped by generation.
        """

        lowest_generation = 0
        groupings: dict[int, set[Self]] = collections.defaultdict(set)

        for generation, user in self.span():
            lowest_generation = min(lowest_generation, generation)
            groupings[generation].add(user)

        while groupings:
            v = groupings.pop(lowest_generation)
            if v is None:
                continue
            yield v

    def to_graphviz_label(
            self,
            name: str | dict[int, str] | None = None,
            custom: CustomTree | None = None,
            escape: bool = True) -> str:
        """
        Convert the user to a Graphviz label.
        """

        name_str: str
        if name is None:
            name_str = str(self.id)
        elif isinstance(name, str):
            name_str = name
        else:
            name_str = name.get(self.id, str(self.id))
        name_str = name_str.replace('"', '\\"')

        if custom:
            return (
                f'{self.id}[label="{name_str}",'
                f'fillcolor={custom.hex["highlighted_node"]},'
                f'fontcolor={custom.hex["highlighted_font"]}];'
            )
        return f'{self.id}[label="{name_str}"];'

    async def to_dot_script(
            self,
            custom: CustomTree) -> str:
        """
        Generates the DOT script from a given generational span.

        Parameters
        ----------
        bot : types.Bot
            The bot instance that should be used to get the names of users.
        customised_tree_user : CustomisedTreeUser
            The customised tree object that should be used to alter how the
            dot script looks.

        Returns
        -------
        str
            The generated DOT code.
        """

        # Get all names that we'll need
        generations = list(self.generation_span())
        all_users = itertools.chain(generations)
        async with db.Database.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM usernames WHERE id = ANY($1::BIGINT[])",
                all_users,
            )
        all_user_names = {}
        for row in rows:
            all_user_names[row["id"]] = row["name"]

        # Set a var
        invisible = "[shape=point,width=0.001,style=invis]"

        # Make some initial digraph stuff
        all_text: str = (
            "digraph {"
            f"node [shape=box,fontcolor={custom.hex['font']},"
            f"color={custom.hex['edge']},"
            f"fillcolor={custom.hex['node']},style=filled];"
            f"edge [dir=none,color={custom.hex['edge']}];"
            f"bgcolor={custom.hex['background']};"
            f"rankdir={custom.hex['direction']};"
        )

        # Go through the members for each generation
        for generation in self.generation_span():

            # Make sure you don't add a spouse twice (as they will
            # be added both by the partner loop and they'll be in the
            # generation list)
            added_already: list[FamilyMember] = []

            # Go through each person in the generation
            for person in generation:

                # Don't add a person twice
                if person in added_already:
                    continue
                added_already.append(person)

                # Work out who the user's partners are
                previous_partner = None
                filtered_possible_partners = [*person.partners]
                for p in filtered_possible_partners.copy():
                    filtered_possible_partners.extend(p.partners)
                filtered_possible_partners = [*list(set(filtered_possible_partners))]
                try:
                    filtered_possible_partners.remove(person)
                except ValueError:
                    pass
                filtered_possible_partners.insert(0, person)

                # Add the user's partners
                all_text += f"subgraph cluster{get_cluster_name()}{{peripheries=0;{{rank=same;"
                for partner in filtered_possible_partners:
                    name = partner.to_graphviz_label(all_user_names, custom)
                    if partner == self:
                        all_text += partner.to_graphviz_label(name, custom)
                    else:
                        all_text += partner.to_graphviz_label(name)
                    if previous_partner is None:
                        previous_partner = partner
                        continue
                    partner_link = f"{previous_partner.id} -> {partner.id};"
                    alt_partner_link = f"{partner.id} -> {previous_partner.id};"
                    if (
                            partner_link not in all_text
                            and alt_partner_link not in all_text
                            and partner != previous_partner):
                        all_text += partner_link
                    added_already.append(partner)
                    previous_partner = partner
                all_text += "}" + "}"

            # Go through the people in the generation and see if they have
            # any children to add
            for person in generation:
                if person._child_ids:
                    all_text += f"p{person.id} {invisible};"

            # Add the lines from parent to node to child
            for person in generation:
                if person._child_ids:
                    new_text = f"{person.id}:s -> p{person.id}:c;"
                    if new_text not in all_text:
                        all_text += new_text
                for child in person.children:
                    new_text = f"p{person.id}:c -> {child.id}:n;"
                    if new_text not in all_text:
                        all_text += new_text

        # And we're done!
        all_text += "}"
        return all_text
