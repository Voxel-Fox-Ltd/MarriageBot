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
        await self.generate_and_send_tree(ctx, custom)

    async def generate_and_send_tree(
            self,
            ctx: n.Interaction,
            custom: u.CustomTree,
            *,
            update_original: bool = False) -> None:
        """
        Generate a tree based on the provided customizations and send it back out into the world.
        """

        tree = await self.generate_tree(custom)
        meth = ctx.send
        if update_original:
            meth = ctx.update
        await meth(
            embeds=u.e(None, image_url="attachment://tree.png"),
            files=[tree],
            components=[
                n.ActionRow([
                    n.Button(
                        "Your text",
                        custom_id=f"CUSTOMISE_TREE {ctx.user.id} highlighted_font {custom.highlighted_font}",
                    ),
                    n.Button(
                        "Your user",
                        custom_id=f"CUSTOMISE_TREE {ctx.user.id} highlighted_node {custom.highlighted_node}",
                    ),
                    n.Button(
                        "Lines",
                        custom_id=f"CUSTOMISE_TREE {ctx.user.id} edge {custom.edge}",
                    ),
                    n.Button(
                        "Users",
                        custom_id=f"CUSTOMISE_TREE {ctx.user.id} node {custom.node}",
                    ),
                    n.Button(
                        "Text",
                        custom_id=f"CUSTOMISE_TREE {ctx.user.id} font {custom.font}",
                    ),
                ]),
                n.ActionRow([
                    n.Button(
                        "Background",
                        custom_id=f"CUSTOMISE_TREE {ctx.user.id} background {custom.background}",
                    ),
                    n.Button(
                        "Direction",
                        custom_id=f"CUSTOMISE_TREE {ctx.user.id} direction {custom.direction}",
                    ),
                ]),
            ]
        )

    @client.event.filtered_component(r"CUSTOMISE_TREE \d+ (.+)")
    async def customize_tree_component(self, ctx: t.ComponentI) -> None:
        """
        Handle the customization of the tree based on the component interaction.
        """

        # Get the customisation type
        _, user_id_str, type_, original = (ctx.custom_id or "").split(" ")
        if user_id_str != str(ctx.user.id):
            return await ctx.send(
                ctx._(
                    "You can't customise someone else's tree! You can customise your own by "
                    "running the {cusomise_command} command :3"
                ).format(cusomise_command=self.customize_tree.get_mention()),
                ephemeral=True,
            )

        # If they're switching directions, just switch em
        if type_ == "direction":
            async with db.Database.acquire() as conn:
                custom = await u.CustomTree.fetch(conn, ctx.user.id)
                custom.direction = "TB" if custom.direction == "LR" else "LR"
                await custom.update(conn)
            return await self.generate_and_send_tree(ctx, custom, update_original=True)

        # Otherwise, we need to send them a modal to deal with
        value = original
        if value == "-1":
            value = "transparent"
        elif value.isdigit():
            value = f"#{int(value):06x}"
        await ctx.send_modal(
            title=ctx._("Customise your tree"),
            custom_id=f"CUSTOMISE_TREE_MODAL {ctx.user.id} {type_}",
            components=[
                n.ActionRow([
                    n.TextInput(
                        label=ctx._("New value"),
                        custom_id="_",
                        style=n.TextInputStyle.SHORT,
                        required=True,
                        value=value,
                    ),
                ]),
            ],
        )

    @client.event.modal
    async def customize_tree_modal(self, ctx: n.Interaction[n.ModalSubmitData]) -> None:
        """
        Handle the modal submission for customizing the tree.
        """

        # Make sure we're dealing with a modal for us
        if not (custom_id := (ctx.custom_id or "")).startswith("CUSTOMISE_TREE_MODAL "):
            return

        # Get the value they entered
        value = ctx.data.components[0].components[0].value.strip()  # pyright: ignore
        _, _, type_ = custom_id.split(" ")

        # Validate the thing they said
        colour = u.colour_to_int(value)
        if colour is None:
            return await ctx.send(
                ctx._("I don't know what colour that is..."),
                ephemeral=True,
            )

        # Validate and update the customisation
        async with db.Database.acquire() as conn:
            custom = await u.CustomTree.fetch(conn, ctx.user.id)
            setattr(custom, type_, colour)
            await custom.update(conn)

        # Regenerate and send the tree
        await self.generate_and_send_tree(ctx, custom, update_original=True)
