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

import random

import aiohttp
import novus as n
from novus import types as t
from novus.ext import client
from novus.ext import database as db
from novus.utils import Localization as LC

from . import utils as u


class Simulation(client.Plugin):

    async def reaction_output(
            self,
            ctx: t.CommandI,
            user: n.User,
            reaction_type: str | None,
            self_strings: list[str],
            other_strings: list[str]) -> None:
        """
        Output a reaction etcetc.
        """

        if user == ctx.user:
            out_raw = random.choice(self_strings)
            out_formatted = out_raw.format(author=ctx.user.mention, user=user.mention)
            return await ctx.send(embeds=u.e(out_formatted))

        if reaction_type:
            image_url = await self.get_reaction_gif(ctx, reaction_type)
        else:
            image_url = None
        out_raw = random.choice(other_strings)
        out_formatted = out_raw.format(author=ctx.user.mention, user=user.mention)
        return await ctx.send(embeds=u.e(out_formatted, image_url))

    async def get_reaction_gif(
            self,
            ctx: t.CommandI,
            reaction_type: str,
            *,
            nsfw: bool = False,
            ignore_checks: bool = False) -> str | None:
        """
        Gets a reaction gif from the Weeb.sh API.

        Parameters
        ----------
        ctx : novus.types.CommandI
            The context for the command.
        reaction_type : str | None
            The type of reaction that you want to get. If not provided,
            then the name of the command in the context is used.
        nsfw : bool, optional
            Whether or not to include NSFW results.
        ignore_checks : bool, optional
            Whether or not to ignore guild checks.

        Returns
        -------
        str | None
            The GIF url.
        """

        # Make sure we have an API key
        if not (api_key := self.bot.config.get("weebsh_api_key")):
            self.log.debug("No API key set for Weeb.sh")
            return None

        # See if we should return anything anyway
        if not ignore_checks:
            if not ctx.guild:
                return None
            async with db.Database.acquire() as conn:
                val = await conn.fetchval(
                    "SELECT gifs_enabled FROM guild_settings WHERE guild_id = $1",
                    ctx.guild.id,
                )
                if val is False:
                    return None

        # Set up our headers and params
        headers = {
            "User-Agent": "MarriageBot (Python aiohttp kae@voxelfox.co.uk)",
            "Authorization": f"Wolke {api_key}"
        }
        params = {
            "type": reaction_type,
            "nsfw": str(nsfw).lower(),
        }

        # Make the request
        async with aiohttp.ClientSession() as session:
            url = "https://api.weeb.sh/images/random"
            async with session.get(url, params=params, headers=headers) as r:
                try:
                    data = await r.json()
                except Exception as e:
                    data = await r.text()
                    self.log.warning(f"Error from Weeb.sh ({e}): {str(data)}")
                    return None
                if r.ok:
                    return data['url']
        return None

    @client.command(
        options=[
            n.ApplicationCommandOption(
                name="user",
                description="The user you want to hug.",
                type=n.ApplicationOptionType.USER,
                # TRANSLATORS: Command option name (/hug [user])
                name_localizations=LC._("user"),
                # TRANSLATORS: Command option description (/hug [user])
                description_localizations=LC._("The user you want to hug."),
            )
        ],
        # TRANSLATORS: Command name (/hug)
        name_localizations=LC._("hug"),
        # TRANSLATORS: Command description (/hug)
        description_localizations=LC._("Hug another user."),
    )
    async def hug(
            self,
            ctx: t.CommandI,
            user: n.User) -> None:
        """
        Hug another user.
        """

        await self.reaction_output(
            ctx, user, "hug",
            [
                ctx._("*You hug yourself... and start crying.*"),
            ],
            [
                ctx._("*Hugs {user}.*"),
            ],
        )

    @client.command(
        options=[
            n.ApplicationCommandOption(
                name="user",
                description="The user you want to ACTION.",
                type=n.ApplicationOptionType.USER,
                # TRANSLATORS: Command option name (/kiss [user])
                name_localizations=LC._("user"),
                # TRANSLATORS: Command option description (/kiss [user])
                description_localizations=LC._("The user you want to ACTION."),
            )
        ],
        # TRANSLATORS: Command name (/kiss)
        name_localizations=LC._("kiss"),
        # TRANSLATORS: Command description (/kiss)
        description_localizations=LC._("Kiss another user."),
    )
    async def kiss(
            self,
            ctx: t.CommandI,
            user: n.User) -> None:
        """
        Kiss another user.
        """

        await self.reaction_output(
            ctx, user, "kiss",
            [
                ctx._("How would you even manage to do that?"),
            ],
            [
                ctx._("*Kisses {user}.*"),
            ],
        )

    @client.command(
        options=[
            n.ApplicationCommandOption(
                name="user",
                description="The user you want to stab.",
                type=n.ApplicationOptionType.USER,
                # TRANSLATORS: Command option name (/stab [user])
                name_localizations=LC._("user"),
                # TRANSLATORS: Command option description (/stab [user])
                description_localizations=LC._("The user you want to stab."),
            )
        ],
        # TRANSLATORS: Command name (/stab)
        name_localizations=LC._("stab"),
        # TRANSLATORS: Command description (/stab)
        description_localizations=LC._("Stab another user."),
    )
    async def stab(
            self,
            ctx: t.CommandI,
            user: n.User) -> None:
        """
        Stab another user.
        """

        await self.reaction_output(
            ctx, user, None,
            [
                ctx._("*You stab yourself.*"),
                ctx._("Looks like you don't have a knife, oops!"),
                ctx._("No."),
            ],
            [
                ctx._("*You stab {user}.*"),
                ctx._("*{user} has been stabbed.*"),
                ctx._("*stabs {user}.*"),
                ctx._("Looks like you don't have a knife, oops!"),
                ctx._("You can't legally stab someone without their consent."),
                ctx._("Stab? Isn't that, like, illegal?"),
                ctx._("I wouldn't recommend doing that tbh."),
            ],
        )

    @client.command(
        options=[
            n.ApplicationCommandOption(
                name="user",
                description="The user you want to ACTION.",
                type=n.ApplicationOptionType.USER,
                # TRANSLATORS: Command option name (/punch [user])
                name_localizations=LC._("user"),
                # TRANSLATORS: Command option description (/punch [user])
                description_localizations=LC._("The user you want to ACTION."),
            )
        ],
        # TRANSLATORS: Command name (/punch)
        name_localizations=LC._("punch"),
        # TRANSLATORS: Command description (/punch)
        description_localizations=LC._("Punch another user."),
    )
    async def punch(
            self,
            ctx: t.CommandI,
            user: n.User) -> None:
        """
        Punch another user.
        """

        await self.reaction_output(
            ctx, user, "punch",
            [
                ctx._("*You punched yourself... for some reason.*"),
            ],
            [
                ctx._("*Punches {user} right in the nose.*"),
            ],
        )

    @client.command(
        options=[
            n.ApplicationCommandOption(
                name="user",
                description="The user you want to ACTION.",
                type=n.ApplicationOptionType.USER,
                # TRANSLATORS: Command option name (/bite [user])
                name_localizations=LC._("user"),
                # TRANSLATORS: Command option description (/bite [user])
                description_localizations=LC._("The user you want to ACTION."),
            )
        ],
        # TRANSLATORS: Command name (/bite)
        name_localizations=LC._("bite"),
        # TRANSLATORS: Command description (/bite)
        description_localizations=LC._("Bite another user."),
    )
    async def bite(
            self,
            ctx: t.CommandI,
            user: n.User) -> None:
        """
        Bite another user.
        """

        await self.reaction_output(
            ctx, user, None,
            [
                ctx._("*You missed and bit yourself! Loser.*"),
                ctx._("*You failed to bite {user}!*"),
                ctx._("*You thought! You bit yourself.*"),
                ctx._("*We'll act like you didn't just bite yourself.*"),
            ],
            [
                ctx._("*You bite {user}.*"),
                ctx._("*Bites {user}.*"),
                ctx._("*{user} was bitten.*"),
                ctx._("*{user} has been bitten.*"),
                ctx._("Why would you bite someone?"),
                ctx._("Biting people isn’t nice."),
                ctx._("Stop biting people!"),
            ],
        )

    @client.command(
        options=[
            n.ApplicationCommandOption(
                name="user",
                description="The user you want to ACTION.",
                type=n.ApplicationOptionType.USER,
                # TRANSLATORS: Command option name (/slap [user])
                name_localizations=LC._("user"),
                # TRANSLATORS: Command option description (/slap [user])
                description_localizations=LC._("The user you want to ACTION."),
            )
        ],
        # TRANSLATORS: Command name (/slap)
        name_localizations=LC._("slap"),
        # TRANSLATORS: Command description (/slap)
        description_localizations=LC._("Slap another user."),
    )
    async def slap(
            self,
            ctx: t.CommandI,
            user: n.User) -> None:
        """
        Slap another user.
        """

        await self.reaction_output(
            ctx, user, "slap",
            [
                ctx._("*You slapped yourself... for some reason.*"),
            ],
            [
                ctx._("*Slaps {user}.*"),
            ],
        )
