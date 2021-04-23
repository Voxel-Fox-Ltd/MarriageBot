from datetime import datetime as dt
import typing

import asyncpg
from discord.ext import commands
import voxelbotutils as utils
import discord

from cogs import utils as localutils



class BotModerator(utils.Cog, command_attrs={'hidden': True}):

    @utils.command()
    @utils.checks.is_bot_support()
    @commands.bot_has_permissions(send_messages=True, add_reactions=True)
    async def runstartupmethod(self, ctx:utils.Context):
        """
        Runs the bot startup method, recaching everything of interest.
        """

        async with ctx.typing():
            await self.bot.startup()
        await ctx.okay()

    @utils.command()
    @utils.checks.is_bot_support()
    @commands.bot_has_permissions(send_messages=True)
    async def copyfamilytoguildwithdelete(self, ctx:utils.Context, user:utils.converters.UserID, guild_id:int):
        """
        Copies a family's span to a given guild ID for server specific families.
        """

        await self.copy_family(ctx, user, guild_id, True)

    @utils.command()
    @utils.checks.is_bot_support()
    @commands.bot_has_permissions(send_messages=True)
    async def copyfamilytoguild(self, ctx:utils.Context, user:utils.converters.UserID, guild_id:int):
        """
        Copies a family's span to a given guild ID for server specific families.
        """

        await self.copy_family(ctx, user, guild_id, False)

    async def copy_family(self, ctx:utils.Context, user_id:int, guild_id:int, delete_members:bool):
        """
        Copy a family to a given Gold guild.
        """

        if guild_id == 0:
            return await ctx.send("No.")

        # Get their current family
        tree = localutils.FamilyTreeMember.get(user_id, guild_id=0)
        users = list(tree.span(expand_upwards=True, add_parent=True))
        await ctx.channel.trigger_typing()

        # Database it to the new guild
        db = await self.bot.database.get_connection()

        # Delete current guild data
        if delete_members:
            await db("DELETE FROM marriages WHERE guild_id=$1", guild_id)
            await db("DELETE FROM parents WHERE guild_id=$1", guild_id)

        # Generate new data to copy
        parents = ((i.id, i._parent, guild_id) for i in users if i._parent)
        partners = ((i.id, i._partner, guild_id) for i in users if i._partner)

        # Push to db
        try:
            await db.conn.copy_records_to_table('parents', columns=['child_id', 'parent_id', 'guild_id'], records=parents)
            await db.conn.copy_records_to_table('marriages', columns=['user_id', 'partner_id', 'guild_id'], records=partners)
        except Exception:
            return await ctx.send("I encountered an error copying that family over.")

        # Send to user
        await ctx.send(f"Copied over `{len(users)}` users. Be sure to run the `runstartupmethod` command")
        await db.disconnect()

    @utils.command()
    @utils.checks.is_bot_support()
    @commands.bot_has_permissions(add_reactions=True)
    async def addserverspecific(self, ctx:utils.Context, guild_id:int, user_id:utils.converters.UserID):
        """
        Adds a guild to the MarriageBot Gold whitelist.
        """

        async with self.bot.database() as db:
            await db(
                """INSERT INTO guild_specific_families (guild_id, purchased_by) VALUES ($1, $2)
                ON CONFLICT (guild_id) DO UPDATE SET purchased_by=excluded.purchased_by""",
                guild_id, user_id,
            )
        await ctx.okay()

    @utils.command()
    @utils.checks.is_bot_support()
    @commands.bot_has_permissions(add_reactions=True)
    async def removeserverspecific(self, ctx:utils.Context, guild_id:int):
        """
        Remove a guild from the MarriageBot Gold whitelist.
        """

        async with self.bot.database() as db:
            await db(
                """DELETE FROM guild_specific_families WHERE guild_id=$1""",
                guild_id,
            )
        await ctx.okay()

    @utils.command(hidden=True)
    @utils.checks.is_bot_support()
    @commands.bot_has_permissions(add_reactions=True)
    async def addship(self, ctx:utils.Context, user1:discord.Member, user2:typing.Optional[discord.Member]=None, percentage:float=0):
        """
        Add a custom ship percentage.
        """

        user2 = user2 or ctx.author
        percentage = max([min([percentage * 100, 10_000]), -10_000])
        async with self.bot.database() as db:
            await db(
                """INSERT INTO ship_percentages (user_id_1, user_id_2, percentage) VALUES ($1, $2, $3)
                ON CONFLICT (user_id_1, user_id_2) DO UPDATE SET percentage=excluded.percentage""",
                *sorted([user1.id, user2.id]), percentage,
            )
        await ctx.okay()

    @utils.command(aliases=['getgoldpurchase'])
    @utils.checks.is_bot_support()
    @commands.bot_has_permissions(send_messages=True)
    async def getgoldpurchases(self, ctx:utils.Context, user:utils.converters.UserID):
        """
        Remove a guild from the MarriageBot Gold whitelist.
        """

        async with self.bot.database() as db:
            rows = await db('SELECT * FROM guild_specific_families WHERE purchased_by=$1', user)
        if not rows:
            return await ctx.send("That user has purchased no instances of MarriageBot Gold.")
        return await ctx.invoke(
            self.bot.get_command("runsql"),
            sql="SELECT * FROM guild_specific_families WHERE purchased_by={}".format(user),
        )

    @utils.command(aliases=['addblogpost'])
    @utils.checks.is_bot_support()
    @commands.bot_has_permissions(send_messages=True)
    async def createblogpost(self, ctx:utils.Context, url:str, title:str, *, content:str=None):
        """
        Adds a blog post to the database.
        """

        if content is None:
            return await ctx.send("You can't send no content.")
        async with self.bot.database() as db:
            await db(
                """INSERT INTO blog_posts VALUES ($1, $2, $3, NOW(), $4) ON CONFLICT (url)
                DO UPDATE SET title=excluded.title, body=excluded.body, created_at=excluded.create_at,
                author_id=excluded.author_id""",
                url, title, content, ctx.author.id,
            )
        await ctx.send(f"Set blog post: https://marriagebot.xyz/blog/{url}", embeddify=False)

    # @utils.command()
    # @utils.checks.is_bot_support()
    # @utils.checks.bot_is_ready()
    # @commands.bot_has_permissions(send_messages=True, attach_files=True)
    # async def treefile(self, ctx:utils.Context, root:utils.converters.UserID=None):
    #     """
    #     Gives you the full family tree of a user.
    #     """

    #     root_user_id = root or ctx.author.id
    #     async with ctx.channel.typing():
    #         text = await localutils.FamilyTreeMember.get(root_user_id, ctx.family_guild_id).generate_gedcom_script(self.bot)
    #     file_bytes = io.BytesIO(text.encode())
    #     await ctx.send(file=discord.File(file_bytes, filename=f'tree_of_{root_user_id}.ged'))


def setup(bot:utils.Bot):
    x = BotModerator(bot)
    bot.add_cog(x)
