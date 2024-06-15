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

import time

from novus import types as t
from novus.ext import client
from novus.ext import database as db

import utils as u


class ProposalHandler(client.Plugin):

    @client.event.filtered_component(r"PROPOSE \w+ \d+ \d+ \d+")
    async def on_propose_button_press(self, ctx: t.ComponentGI) -> None:
        """
        Pinged when a propose message is pressed.
        """

        # Get relevant args
        _, action, accepted_str, author_id_str, user_id_str, timeout_str = \
            ctx.data.custom_id.split(" ")
        author_id, user_id, timeout = u.mint(author_id_str, user_id_str, timeout_str)
        guild_id: int = ctx.guild.id if self.bot.config.gold else 0
        accepted = accepted_str == "1"

        # See if the user is allowed to press buttons on this message
        if ctx.user.id not in [author_id, user_id]:
            return await ctx.send(
                ctx._("You cannot interact with these buttons."),
                ephemeral=True,
            )

        # See if the proposal has timed out
        if time.time() > timeout:
            await ctx.send(
                ctx._("You can no longer respond to this message."),
                ephemeral=True,
            )
            try:
                await ctx.message.delete()
            except Exception:
                pass
            return

        # See if the given starting user selected their own accept button
        if accepted and ctx.user.id == author_id:
            return await ctx.send(
                ctx._("You can't accept your own proposal!"),
                ephemeral=True,
            )

        # Starting user cancelled their own proposal
        elif not accepted and ctx.user.id == author_id:
            u.ProposalLock.unlock(author_id, user_id)
            u.AutoDelete.cancel(ctx.message)
            return await ctx.update(
                content=None,
                embeds=u.e(
                    ctx._("Alright, {author}, your proposal to {user} has been cancelled :)")
                    .format(author=f"<@{author_id}>", user=f"<@{user_id}>")
                ),
                components=None,
            )

        # Target user said no to the proposal
        elif not accepted:
            u.ProposalLock.unlock(author_id, user_id)
            u.AutoDelete.cancel(ctx.message)
            return await ctx.update(
                content=None,
                embeds=u.e(
                    ctx._("Sorry, {author}, {user} said no to your proposal :<")
                    .format(author=f"<@{author_id}>", user=f"<@{user_id}>")
                ),
                components=None,
            )

        # See what they want to do
        author_ft, user_ft = u.FamilyMember.get_multiple(
            author_id, user_id, guild_id=guild_id,
        )
        async with db.Database.acquire() as conn:
            match action:
                case "MARRY":
                    await author_ft.db.add_partner(conn, user_ft)
                case "ADOPT":
                    await author_ft.db.add_child(conn, user_ft)
                case "MAKEPARENT":
                    await author_ft.db.add_parent(conn, user_ft)
                case _:
                    raise NotImplementedError("Invalid action type")

        # Generic response output
        u.ProposalLock.unlock(author_id, user_id)
        u.AutoDelete.cancel(ctx.message)
        message: str = {
            "MARRY": ctx._("Welcome {user}! You're now married to {author} :3c"),
            "ADOPT": ctx._("Welcome to the family, {user}! You're now the child of {author} :3c"),
            "MAKEPARENT": ctx._("Welcome to the family, {user}! You're now the parent of {author} :3c"),
        }[action]
        return await ctx.update(
            content=None,
            embeds=u.e(message.format(user=f"<@{user_id}>", author=f"<@{author_id}>")),
            components=None,
        )
