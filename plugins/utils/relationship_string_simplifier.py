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

import re

__all__ = (
    "simplify_relationship",
)


class RelationshipStringSimplifier:
    """
    Simplifies complex relationship strings into standard family terms
    using mostly regex substitutions.
    """

    _REGEX_REPLACEMENTS = [
        # Preprocessing / flattening
        (r"parent's partner", "parent"),
        (r"partner's child", "child"),
        (r"child's parent", ""),
        (r"\s+'s", ""),       # space before possessive
        (r"'s", ""),          # standalone possessive
        (r"\s{2,}", " "),     # multiple spaces

        # Relationship replacements
        (r"sibling's partner's child", "niece/nephew"),
        (r"parent's sibling", "aunt/uncle"),
        (r"aunt/uncle's child", "cousin"),
        (r"parent's child", "sibling"),
        (r"sibling's child", "niece/nephew"),
        (r"parent's niece/nephew", "cousin"),
        (r"niece/nephew's sibling", "niece/nephew"),
        (r"niece/nephew's child", "grandniece/nephew"),
        (r"grandgrandniece/nephew", "great grandniece/nephew"),
        (r"partner's parent", "parent-in-law"),
        (r"grandsibling", "great aunt/uncle"),
        (r"sibling's (\d+(?:st|nd|rd|th) cousin)", r"\1"),
    ]

    _COUSIN_PATTERN = re.compile(
        r"(?:parent's)(?: (?:parent|child)(?:'s)?)+ child"
    )

    @classmethod
    def _apply_regex_replacements(cls, text: str) -> str:
        for pattern, repl in cls._REGEX_REPLACEMENTS:
            text = re.sub(pattern, repl, text)
        return text.strip()

    @classmethod
    def _apply_generation_reductions(cls, text: str) -> str:
        # "child's child's child" → "great grandchild"
        text = re.sub(
            r"((?:child's )+)child",
            lambda m: ("great " * (m.group(1).count(" ") - 1)) + "grandchild",
            text,
        )
        # "parent's parent's parent" → "great grandparent"
        text = re.sub(
            r"((?:parent's )+)parent",
            lambda m: ("great " * (m.group(1).count(" ") - 1)) + "grandparent",
            text,
        )
        return text

    @classmethod
    def _get_cousin_string(cls, match: re.Match) -> str:
        path = match.group(0)
        p = path.count("parent")
        c = path.count("child")

        if p < 2:
            return path
        if c == 1:
            return "aunt/uncle" if p <= 2 else f"{'great ' * (p - 3)}grand aunt/uncle"

        # nth cousin x times removed logic
        p -= 2
        c -= 2
        nth = min(c + 1, p + 1)
        removed = abs(p - c)

        if nth < 1:
            return path

        if nth % 10 == 1 and nth != 11:
            ordinal = f"{nth}st"
        elif nth % 10 == 2 and nth != 12:
            ordinal = f"{nth}nd"
        elif nth % 10 == 3 and nth != 13:
            ordinal = f"{nth}rd"
        else:
            ordinal = f"{nth}th"

        result = f"{ordinal} cousin"
        if removed == 1:
            result += " 1 time removed"
        elif removed > 1:
            result += f" {removed} times removed"
        return result

    @classmethod
    def simplify(cls, text: str) -> str:
        text = text.strip()

        for _ in range(3):  # Multiple passes to settle replacements
            text = cls._apply_regex_replacements(text)
            text = cls._COUSIN_PATTERN.sub(cls._get_cousin_string, text)
            text = cls._apply_generation_reductions(text)
            text = text.strip()

        return text


simplify_relationship = RelationshipStringSimplifier.simplify
