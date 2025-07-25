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
import os
import pathlib
import uuid

import novus as n
from novus import types as t
from novus.ext import client
from novus.ext import database as db
from novus.utils import Localization as LC

from . import utils as u


class Customisation(client.Plugin):

    TREE_FOLDER = pathlib.Path("./_temp/")

    async def generate_tree(self, custom: u.CustomTree) -> n.File:
        """
        Generate a tree from a set of customisations and return its file handle.
        """

        family_member = u.FamilyMember.get(0, 0)

        # Get their dot script
        try:
            dot_code = await asyncio.wait_for(
                family_member.to_dot_script(custom),
                timeout=10.0,
            )
        except asyncio.TimeoutError:
            self.log.error("Failed to create dot script within 10 seconds.")
            raise

        # Write the dot to a file
        filename_id = str(uuid.uuid4())
        dot_filename = self.TREE_FOLDER / f"{filename_id}.gz"
        os.makedirs(self.TREE_FOLDER, exist_ok=True)
        try:
            with open(dot_filename, 'w', encoding='utf-8') as a:
                a.write(dot_code)
        except Exception as e:
            self.log.error(f"Could not write to {dot_filename}")
            raise e

        # Convert to an image
        image_filename = self.TREE_FOLDER / f"{filename_id}.png"
        format_rendering_option = "-Tpng:cairo"  # normal colour, and antialising

        dot = await asyncio.create_subprocess_exec(
            "dot",
            format_rendering_option,
            dot_filename,
            "-o",
            image_filename,
            "-Gcharset=UTF-8",
        )
        await asyncio.wait_for(dot.wait(), 30.0)

        # Kill subprocess
        try:
            dot.kill()
        except ProcessLookupError:
            pass  # It already died
        except Exception:
            raise

        # Send file
        try:
            file = n.File(image_filename, filename="tree.png")
        except FileNotFoundError:
            raise

        async def delete_soon() -> None:
            await asyncio.sleep(10)
            asyncio.create_task(asyncio.create_subprocess_exec("rm", dot_filename))
            asyncio.create_task(asyncio.create_subprocess_exec("rm", image_filename))

        asyncio.create_task(delete_soon())

        return file

    @client.command(
        name="customize-tree",
        description="Customise the look of your family trees.",
        # TRANSLATORS: Command name
        name_localizations=LC._("customize-tree"),
        # TRANSLATORS: Command description
        description_localizations=LC._("Customize the look of your family trees."),
    )
    async def customize_tree(self, ctx: t.CommandI) -> None:
        """
        Command to customize the look of family trees.
        """

        await ctx.defer()

        # Create a tree for them
        async with db.Database.acquire() as conn:
            custom = await u.CustomTree.fetch(conn, ctx.user.id)
        tree = await self.generate_tree(custom)
        await ctx.send(
            embeds=u.e(None, image_url="attachment://tree.png"),
            files=[tree],
            components=[
                n.ActionRow([
                    n.Button(
                        "edge",
                        custom_id=f"CUSTOMISE_TREE {ctx.user.id} edge",
                    ),
                    n.Button(
                        "node",
                        custom_id=f"CUSTOMISE_TREE {ctx.user.id} node",
                    ),
                    n.Button(
                        "font",
                        custom_id=f"CUSTOMISE_TREE {ctx.user.id} font",
                    ),
                    n.Button(
                        "highlighted_font",
                        custom_id=f"CUSTOMISE_TREE {ctx.user.id} highlighted_font",
                    ),
                    n.Button(
                        "highlighted_node",
                        custom_id=f"CUSTOMISE_TREE {ctx.user.id} highlighted_node",
                    ),
                ]),
                n.ActionRow([
                    n.Button(
                        "background",
                        custom_id=f"CUSTOMISE_TREE {ctx.user.id} background",
                    ),
                    n.Button(
                        "direction",
                        custom_id=f"CUSTOMISE_TREE {ctx.user.id} direction",
                    ),
                ]),
            ]
        )
