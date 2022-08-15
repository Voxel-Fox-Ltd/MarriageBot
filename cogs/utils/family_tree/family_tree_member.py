from __future__ import annotations

import random
import string
from typing import (
    TYPE_CHECKING,
    Dict,
    Tuple,
    List,
    Optional,
    Iterable,
    Union,
    Set,
    overload,
    Literal,
)

from cogs.utils import types
from cogs.utils.customised_tree_user import CustomisedTreeUser
from cogs.utils.family_tree.relationship_string_simplifier import RelationshipStringSimplifier as Simplifier
from cogs.utils.discord_name_manager import DiscordNameManager

if TYPE_CHECKING:
    import discord
    FamilyTreeMemberSetter = Union[
        "FamilyTreeMember",
        int,
        discord.User,
        discord.Member,
    ]


def sort_generation(generation: List[FamilyTreeMember]) -> List[FamilyTreeMember]:
    """
    Sort a list of family tree members into groups of
    [USER, PARTNER, PARTNER]... to make them easier to just throw into a
    DOT script.
    """

    new_generation: List[FamilyTreeMember] = list()
    for person in sorted(generation, key=lambda p: p.id):
        if person not in new_generation:
            new_generation.append(person)
        for partner in person.partners:
            if partner in generation and partner not in new_generation:
                new_generation.append(person)
    return new_generation


class FamilyTreeMember:
    """
    A class representing a member of a family.
    """

    all_users: Dict[Tuple[int, int], FamilyTreeMember] = {}
    INVISIBLE = "[shape=circle, label=\"\", height=0.001, width=0.001]"  # For the DOT script

    __slots__ = (
        'id',
        '_children',
        '_parent',
        '_partners',
        '_guild_id',
    )

    def __init__(
            self,
            discord_id: int,
            children: Optional[List[int]] = None,
            parent_id: Optional[int] = None,
            partners: Optional[List[int]] = None,
            guild_id: int = 0):
        self.id: int = discord_id
        self._children: List[int] = children or list()
        self._parent: Optional[int] = parent_id
        self._partners: List[int] = partners or list()
        self._guild_id: int = guild_id
        self.all_users[(self.id, self._guild_id)] = self

    def __hash__(self):
        return hash((self.id, self._guild_id,))

    @overload
    def _get_user_id(self, value: FamilyTreeMemberSetter) -> int:
        ...

    @overload
    def _get_user_id(self, value: None) -> None:
        ...

    def _get_user_id(self, value: Optional[FamilyTreeMemberSetter]) -> Optional[int]:
        if value is None:
            return None
        if isinstance(value, int):
            return value
        return value.id

    @classmethod
    def get(
            cls,
            discord_id: int,
            guild_id: int = 0) -> FamilyTreeMember:
        """
        Gives you the object pertaining to the given user ID.

        Parameters
        ----------
        discord_id : int
            The ID of the Discord user we want to get the information off.
        guild_id : int, optional
            The ID of the guild that we want to get the user from.

        Returns
        -------
        FamilyTreeMember
            The family member we've queried for.
        """

        assert discord_id
        v = cls.all_users.get((discord_id, guild_id))
        if v:
            return v
        return cls(
            discord_id=discord_id,
            guild_id=guild_id,
        )

    @classmethod
    def get_multiple(
            cls,
            *discord_ids: int,
            guild_id: int = 0) -> Iterable[FamilyTreeMember]:
        """
        Gets multiple objects from the cache.
        """

        for i in discord_ids:
            yield cls.get(i, guild_id)

    @overload
    def add_child(
            self,
            child: FamilyTreeMemberSetter,
            *,
            return_added: Literal[True]) -> FamilyTreeMember:
        ...

    @overload
    def add_child(
            self,
            child: FamilyTreeMemberSetter,
            *,
            return_added: Literal[False] = False) -> None:
        ...

    def add_child(
            self,
            child: FamilyTreeMemberSetter,
            *,
            return_added: bool = False) -> Optional[FamilyTreeMember]:
        """
        Add a new child to this user's children list.
        """

        child_id = self._get_user_id(child)
        if child_id not in self._children:
            self._children.append(child_id)

        if return_added:
            return self.get(child_id, self._guild_id)

    @overload
    def remove_child(
            self,
            child: FamilyTreeMemberSetter,
            *,
            return_added: Literal[True]) -> FamilyTreeMember:
        ...

    @overload
    def remove_child(
            self,
            child: FamilyTreeMemberSetter,
            *,
            return_added: Literal[False] = False) -> None:
        ...

    def remove_child(
            self,
            child: FamilyTreeMemberSetter,
            *,
            return_added: bool = False) -> Optional[FamilyTreeMember]:
        """
        Remove a child from this user's children list.
        """

        child_id = self._get_user_id(child)
        while child_id in self._children:
            self._children.remove(child_id)

        if return_added:
            return self.get(child_id, self._guild_id)

    @overload
    def add_partner(
            self,
            partner: FamilyTreeMemberSetter,
            *,
            return_added: Literal[True]) -> FamilyTreeMember:
        ...

    @overload
    def add_partner(
            self,
            partner: FamilyTreeMemberSetter,
            *,
            return_added: Literal[False] = False) -> None:
        ...

    def add_partner(
            self,
            partner: FamilyTreeMemberSetter,
            *,
            return_added: bool = False) -> Optional[FamilyTreeMember]:
        """
        Add a new partner to this user's partner list.
        """

        partner_id = self._get_user_id(partner)
        if partner_id not in self._partners:
            self._partners.append(partner_id)

        if return_added:
            return self.get(partner_id, self._guild_id)

    @overload
    def remove_partner(
            self,
            partner: FamilyTreeMemberSetter,
            *,
            return_added: Literal[True]) -> FamilyTreeMember:
        ...

    @overload
    def remove_partner(
            self,
            partner: FamilyTreeMemberSetter,
            *,
            return_added: Literal[False] = False) -> None:
        ...

    def remove_partner(
            self,
            partner: FamilyTreeMemberSetter,
            *,
            return_added: bool = False) -> Optional[FamilyTreeMember]:
        """
        Remove a partner from this user's partner list.
        """

        partner_id = self._get_user_id(partner)
        while partner_id in self._partners:
            self._partners.remove(partner_id)

        if return_added:
            return self.get(partner_id, self._guild_id)

    def to_json(self) -> dict:
        """
        Converts the object to JSON format so you can throw it through Redis.
        """

        return {
            "discord_id": self.id,
            "children": self._children,
            "parent_id": self._parent,
            "partners": self._partners,
            "guild_id": self._guild_id,
        }

    @classmethod
    def from_json(cls, data: dict) -> FamilyTreeMember:
        """
        Loads an FamilyTreeMember object from JSON.

        Parameters
        ----------
        data : dict
            The JSON object that represent the FamilyTreeMember object.

        Returns
        -------
        FamilyTreeMember
            The new FamilyTreeMember object.
        """

        return cls(**data)

    def __repr__(self) -> str:
        attrs = (
            ("discord_id", "id",),
            ("children", "_children",),
            ("parent_id", "_parent",),
            ("partners", "_partners",),
            ("guild_id", "_guild_id",),
        )
        d = ", ".join(["%s=%r" % (i, getattr(self, o)) for i, o in attrs])
        return f"{self.__class__.__name__}({d})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return all([
            self.id == other.id,
            self._guild_id == other._guild_id,
        ])

    @property
    def parent(self) -> Optional[FamilyTreeMember]:
        """
        Gets you the instance of this user's parent.
        """

        if self._parent and self._parent != self.id:
            return self.get(self._parent, self._guild_id)
        return None

    @parent.setter
    def parent(self, value: Optional[FamilyTreeMemberSetter]):
        self._parent = self._get_user_id(value)

    @property
    def children(self) -> Iterable[FamilyTreeMember]:
        """
        Gets you the list of children instances for this user.
        """

        for i in sorted(self._children):
            if i == self.id:
                continue
            yield self.get(i, self._guild_id)

    @children.setter
    def children(self, value: Iterable[FamilyTreeMemberSetter]):
        self._children = [self._get_user_id(i) for i in value]

    @property
    def partners(self) -> Iterable[FamilyTreeMember]:
        """
        Gets you the list of partner instances for this user.
        """

        for i in sorted(self._partners):
            if i == self.id:
                continue
            yield self.get(i, self._guild_id)

    @partners.setter
    def partners(self, value: Iterable[FamilyTreeMemberSetter]):
        self._partners = [self._get_user_id(i) for i in value]

    def get_direct_relations(self) -> List[int]:
        """
        Gets the direct relation IDs for the given user.
        """

        output = []
        output.extend(self._children)
        output.append(self._parent)
        output.extend(self._partners)
        return [i for i in output if i is not None]

    @property
    def is_empty(self) -> bool:
        """
        Does this instance have any family members? Does not check
        for loops etc, and is only used before a tree generation.
        """

        return not any((
            len(self._partners) > 0,
            self._parent is not None,
            len(self._children) > 0
        ))

    def get_relation(self, target_user: FamilyTreeMember) -> Optional[str]:
        """
        Gets your relation to another given FamilyTreeMember object.

        Parameters
        ----------
        target_user : FamilyTreeMember
            The user who we want to get the relationship to.

        Returns
        -------
        Optional[str]
            The family tree relationship string.
        """

        text = self.get_unshortened_relation(target_user)
        if text is None:
            return None
        return Simplifier().simplify(text)

    @property
    def family_member_count(self) -> int:
        """
        Returns the number of people in the family.
        """

        family_member_count = 0
        for _ in self.span(add_parent=True, expand_upwards=True):
            family_member_count += 1
        return family_member_count

    def span(
            self,
            people_list: Union[set, None] = None,
            add_parent: bool = False,
            expand_upwards: bool = False) -> Iterable[FamilyTreeMember]:
        """
        Gets a list of every user related to this one
        If "add_parent" and "expand_upwards" are True, then it should
        add every user in a given tree, even if they're related through
        marriage's parents etc.

        Parameters
        ----------
        people_list : set, optional
            The list of users who are currently in the tree (so as to avoid recursion)
        add_parent : bool, optional
            Whether or not to add the parent of this user to the people list
        expand_upwards : bool, optional
            Whether or not to expand upwards in the tree

        Yields
        ------
        Iterable[FamilyTreeMember]
            A list of users that this person is related to.
        """

        # Don't add yourself again
        if people_list is None:
            people_list = set()
        if self in people_list:
            return people_list
        people_list.add(self)
        yield self

        # Add your parent
        if expand_upwards and add_parent and self._parent:
            assert self.parent
            yield from self.parent.span(
                people_list,
                add_parent=True,
                expand_upwards=expand_upwards,
            )

        # Add your children
        for child in self.children:
            yield from child.span(
                people_list,
                add_parent=False,
                expand_upwards=expand_upwards,
            )

        # Add your partner
        for partner in self.partners:
            yield from partner.span(
                people_list,
                add_parent=True,
                expand_upwards=expand_upwards,
            )

    def get_root(self) -> FamilyTreeMember:
        """
        Expands backwards into the tree up to a root user.
        Only goes up one line of family so it cannot add your spouse's parents etc.
        """

        # Set a default user to look at
        root_user = self
        already_processed = set()

        # Loop until we get someone
        while True:

            # The person we're looking at has been processed before,
            # and as such they should be the top of our tree
            if root_user in already_processed:
                return root_user

            # Keep track of people we've looked at already
            already_processed.add(root_user)

            # If this user has a parent, they must be higher than
            # this instance by default
            if root_user._parent:
                assert root_user.parent
                root_user = root_user.parent

            # If they have any partners, one of THEM could have a parent
            elif root_user._partners:

                # Have to iterate through them to get the cached values
                for p in root_user.partners:

                    # See if a partner has a parent
                    if p._parent:
                        assert p.parent
                        root_user = p.parent
                        break

            # If this user has no parents or partners, they must be the
            # top of our tree
            else:
                return root_user

    def get_unshortened_relation(
            self,
            target_user: FamilyTreeMember,
            working_relation: Union[List[str], None] = None,
            added_already: Union[Set[int], None] = None) -> Optional[str]:
        """
        Gets your relation to the other given user.

        Args:
            target_user (FamilyTreeMember): The user who you want to list the relation to.
            working_relation (list, optional): The list of relation steps it's taking to get.
            added_already (list, optional): So we can keep track of who's been looked at before.

        Returns:
            Optional[str]: The family tree relationship string.
        """

        # Set default values
        if working_relation is None:
            working_relation = []
        if added_already is None:
            added_already = set()

        # You're doing a loop - return None
        if self.id in added_already:
            return None

        # We hit the jackpot - return the made up string
        if target_user.id == self.id:
            ret_string = "'s ".join(working_relation)
            return ret_string

        # Add self to list of checked people
        added_already.add(self.id)

        # Check parent
        if self._parent and self._parent not in added_already:
            parent = self.parent
            assert parent
            x = parent.get_unshortened_relation(
                target_user,
                working_relation=working_relation + ['parent'],
                added_already=added_already
            )
            if x:
                return x

        # Check partner
        for i in [o for o in self.partners if o.id not in added_already]:
            x = i.get_unshortened_relation(
                target_user,
                working_relation=working_relation + ['partner'],
                added_already=added_already
            )
            if x:
                return x

        # Check children
        for i in [o for o in self.children if o.id not in added_already]:
            x = i.get_unshortened_relation(
                target_user,
                working_relation=working_relation + ['child'],
                added_already=added_already
            )
            if x:
                return x

        return None

    def generational_span(
            self,
            people_dict: Union[Dict[int, List[FamilyTreeMember]], None] = None,
            depth: int = 0,
            add_parent: bool = False,
            add_partners: bool = True,
            expand_upwards: bool = False,
            all_people: Union[set, None] = None,
            recursive_depth: int = 0) -> Dict[int, List[FamilyTreeMember]]:
        """
        Gets a list of every user related to this one.
        If "add_parent" and "expand_upwards" are True, then it
        should add every user in a given tree, even if they're
        related through marriage's parents etc.

        Parameters
        ----------
        people_dict : Union[dict, None], optional
            The dict of users who are currently in the tree
            (so as to avoid recursion).
        depth : int, optional
            The current generation of the tree span.
        add_parent : bool, optional
            Whether or not to add the parent of this user to the
            people list.
        expand_upwards : bool, optional
            Whether or not to expand upwards in the tree.
        all_people : Union[set, None], optional
            A set of all people who this recursive function would
            look at.
        recursive_depth : int, optional
            How far into the recursion you have gone - this is so we
            don't get recursion errors.

        Returns
        -------
        Dict[int, List[FamilyTreeMember]]
            A dictionary of each generation of users.
        """

        # Don't add yourself again
        if people_dict is None:
            people_dict = {}
        if all_people is None:
            all_people = set()
        if self.id in all_people:
            return people_dict
        if recursive_depth >= 500:
            return people_dict
        all_people.add(self.id)

        # Add to dict
        x = people_dict.setdefault(depth, list())
        x.append(self)

        # Add your children
        for child in self.children:
            people_dict = child.generational_span(
                people_dict,
                depth=depth + 1,
                add_parent=False,
                add_partners=True,
                expand_upwards=expand_upwards,
                all_people=all_people,
                recursive_depth=recursive_depth + 1,
            )

        # Add your partner
        if add_partners:
            for partner in self.partners:
                people_dict = partner.generational_span(
                    people_dict,
                    depth=depth,
                    add_parent=True,
                    add_partners=False,
                    expand_upwards=expand_upwards,
                    all_people=all_people,
                    recursive_depth=recursive_depth + 1,
                )

        # Add your parent
        if expand_upwards and add_parent and self._parent:
            parent = self.parent
            assert parent
            people_dict = parent.generational_span(
                people_dict,
                depth=depth - 1,
                add_parent=True,
                add_partners=True,
                expand_upwards=expand_upwards,
                all_people=all_people,
                recursive_depth=recursive_depth + 1,
            )

        # Remove dupes, should they be in there
        return people_dict

    async def to_dot_script(
            self,
            bot: types.Bot,
            customised_tree_user: CustomisedTreeUser) -> str:
        """
        Gives you a string of the current family tree that will go through DOT.

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

        root_user = self.get_root()
        gen_span = root_user.generational_span()
        return await self.to_dot_script_from_generational_span(bot, gen_span, customised_tree_user)

    async def to_full_dot_script(
            self,
            bot: types.Bot,
            customised_tree_user: CustomisedTreeUser) -> str:
        """
        Gives you the string of the FULL current family.

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

        root_user = self.get_root()
        gen_span = root_user.generational_span(expand_upwards=True, add_parent=True)
        return await self.to_dot_script_from_generational_span(bot, gen_span, customised_tree_user)

    async def to_dot_script_from_generational_span(
            self,
            bot: types.Bot,
            gen_span: Dict[int, List[FamilyTreeMember]],
            customised_tree_user: CustomisedTreeUser) -> str:
        """
        Generates the DOT script from a given generational span.

        Parameters
        ----------
        bot : types.Bot
            The bot instance that should be used to get the names of users.
        gen_span : Dict[int, List[FamilyTreeMember]]
            The generational span.
        customised_tree_user : CustomisedTreeUser
            The customised tree object that should be used to alter how the
            dot script looks.

        Returns
        -------
        str
            The generated DOT code.
        """

        # Find my own depth
        my_depth: int = 0
        for depth, depth_list in gen_span.items():
            if self in depth_list:
                my_depth = depth
                break

        # Add my partner and parent
        for partner in self.partners:
            if partner not in (x := gen_span.get(my_depth, list())):
                x.append(partner)
                gen_span[my_depth] = x
        if (parent := self.parent):
            if parent not in (x := gen_span.get(my_depth - 1, list())):
                x.append(parent)
                gen_span[my_depth - 1] = x

        # Long var names suck
        ctu = customised_tree_user

        # Make some initial digraph stuff
        all_text: str = (
            "digraph {"
            f"node [shape=box,fontcolor={ctu.hex['font']},"
            f"color={ctu.hex['edge']},"
            f"fillcolor={ctu.hex['node']},style=filled];"
            f"edge [dir=none,color={ctu.hex['edge']}];"
            f"bgcolor={ctu.hex['background']};"
            f"rankdir={ctu.hex['direction']};"
        )

        # Set up some stuff for later
        added_users: Set[FamilyTreeMember] = set()  # A list of people in this dot graph

        # Add the username for each user (from unflattened list)
        for generation in gen_span.values():

            # Go through each person in a generation to add their name
            for i in generation:

                # Get their name and ignore if they don't have one
                name = await DiscordNameManager.fetch_name_by_id(bot, i.id)
                name = name.replace('"', '\\"')

                # Generate dot for both ourselves and others
                if i == self:
                    all_text += (
                        f'{i.id}[label="{name}",'
                        f'fillcolor={ctu.hex["highlighted_node"]},'
                        f'fontcolor={ctu.hex["highlighted_font"]}];'
                    )
                else:
                    all_text += f'{i.id}[label="{name}"];'

        # The ordered list of generation numbers -
        # just a list of sequential numbers
        # Done so we can make sure we have each generation in the
        # right order
        generation_numbers: List[int] = sorted(list(gen_span.keys()))

        # Go through the members for each generation
        for _, generation_number in enumerate(generation_numbers):
            if (generation := gen_span.get(generation_number)) is None:
                continue
            generation = sort_generation(generation)

            # Make sure you don't add a spouse twice (as they will
            # be added both by the partner loop and they'll be in the
            # generation list)
            added_already: List[FamilyTreeMember] = []

            # Add a ranking for this generation; only necessary if this
            # if our first runthrough (the child adding section adds this
            # on subsequent loops)
            all_text += "{rank=same;"

            # Add linking
            previous_person = None

            # Go through each person in the generation
            for person in generation:

                # Don't add a person twice
                if person in added_already:
                    continue
                added_already.append(person)

                # Make sure they stay in line
                if previous_person:
                    all_text += f"{previous_person.id} -> {person.id} [style=invis];"

                # Add the user and their partner
                previous_partner = person
                for partner in person.partners:
                    if partner in generation:
                        all_text += f"{previous_partner.id} -> {partner.id};"
                        added_already.append(partner)
                        previous_partner = partner

                # No partner, so they weren't added to the graph
                if not person._partners:
                    all_text += f"{person.id};"
                    previous_person = person

            # Close off the generation and open a new ranking for
            # adding children links
            all_text += "}{"

            # Go through the people in the generation and see if they have
            # any children to add
            for person in generation:
                if person._children:
                    all_text += f"p{person.id} {self.INVISIBLE};"
            all_text += "}"

            # Add the lines from parent to node to child
            for person in generation:
                if person._children:
                    new_text = f"{person.id} -> p{person.id};"
                    if new_text not in all_text:
                        all_text += new_text
                for child in person.children:
                    new_text = f"p{person.id} -> {child.id};"
                    if new_text not in all_text:
                        all_text += new_text

        # And we're done!
        all_text += "}"
        return all_text
