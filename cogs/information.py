import asyncio
import typing
import io
from datetime import datetime as dt

import discord
from discord.ext import commands

from cogs import utils


class Information(utils.Cog):

    @commands.command(aliases=['spouse', 'husband', 'wife', 'marriage'], cls=utils.Command)
    @utils.cooldown.cooldown(1, 5, commands.BucketType.user)
    @utils.checks.bot_is_ready()
    @commands.bot_has_permissions(send_messages=True)
    async def partner(self, ctx:utils.Context, user:typing.Optional[utils.converters.UserID]):
        """Tells you who a user is married to"""

        # Get the user's info
        user = user or ctx.author.id
        user_name = await self.bot.get_name(user)
        user_info = utils.FamilyTreeMember.get(user, ctx.family_guild_id)

        # Check they have a partner
        if user_info._partner is None:
            return await ctx.send(f"`{user_name}` is not currently married.")
        partner_name = await self.bot.get_name(user_info._partner)

        # Get timestamp
        async with self.bot.database() as db:
            if self.bot.is_server_specific:
                data = await db("SELECT * FROM marriages WHERE user_id=$1 AND guild_id<>0", user)
            else:
                data = await db("SELECT * FROM marriages WHERE user_id=$1 AND guild_id=0", user)
        try:
            timestamp = data[0]['timestamp']
        except IndexError:
            timestamp = None

        # Output
        if timestamp:
            await ctx.send(f"`{user_name}` is currently married to `{partner_name}` (`{user_info._partner}`). They've been married since {timestamp.strftime('%B %d %Y')}.")
        else:
            await ctx.send(f"`{user_name}` is currently married to `{partner_name}` (`{user_info._partner}`).")

    @commands.command(aliases=['child', 'kids'], cls=utils.Command)
    @utils.cooldown.cooldown(1, 5, commands.BucketType.user)
    @utils.checks.bot_is_ready()
    @commands.bot_has_permissions(send_messages=True)
    async def children(self, ctx:utils.Context, user:utils.converters.UserID=None):
        """Tells you who a user's children are"""

        # Setup output variable
        output = ''

        # Get the user's info
        user = user or ctx.author.id
        user_name = await self.bot.get_name(user)
        user_info = utils.FamilyTreeMember.get(user, ctx.family_guild_id)

        # Get user's children
        if len(user_info._children) == 0:
            output += f"`{user_name}` has no children right now."
        else:
            ren = {False:"ren", True:""}[len(user_info._children) == 1]
            output += f"`{user_name}` has `{len(user_info._children)}` child{ren}: "
            children = [(await self.bot.get_name(i), i) for i in user_info._children]
            output += ", ".join([f"`{i[0]}` (`{i[1]}`)" for i in children]) + "."

        # Do they have a partner?
        if user_info._partner is None:
            return await ctx.send(output)

        # Get their partner's children
        user_info = user_info.partner
        user_name = await self.bot.get_name(user_info.id)
        if len(user_info._children) == 0:
            output += f"\n\nTheir partner, `{user_name}`, has no children right now."
        else:
            ren = {False:"ren", True:""}[len(user_info._children) == 1]
            output += f"\n\nTheir partner, `{user_name}`, has `{len(user_info._children)}` child{ren}: "
            children = [(await self.bot.get_name(i), i) for i in user_info._children]
            output += ", ".join([f"`{i[0]}` (`{i[1]}`)" for i in children]) + "."

        # Return all output
        await ctx.send(output)

    @commands.command(aliases=['parents'], cls=utils.Command)
    @utils.cooldown.cooldown(1, 5, commands.BucketType.user)
    @utils.checks.bot_is_ready()
    @commands.bot_has_permissions(send_messages=True)
    async def parent(self, ctx:utils.Context, user:utils.converters.UserID=None):
        """Tells you who someone's parent is"""

        user = user or ctx.author.id
        user_info = utils.FamilyTreeMember.get(user, ctx.family_guild_id)
        user_name = await self.bot.get_name(user)
        if user_info._parent is None:
            await ctx.send(f"`{user_name}` has no parent.")
            return
        name = await self.bot.get_name(user_info._parent)
        await ctx.send(f"`{user_name}`'s parent is `{name}` (`{user_info._parent}`).")

    @commands.command(aliases=['relation'], cls=utils.Command)
    @utils.cooldown.cooldown(1, 5, commands.BucketType.user)
    @utils.checks.bot_is_ready()
    @commands.bot_has_permissions(send_messages=True)
    async def relationship(self, ctx:utils.Context, user:utils.converters.UserID, other:utils.converters.UserID=None):
        """Gets the relationship between the two specified users"""

        # Check against themselves
        if (user == ctx.author and other is None) or (user == other):
            return await ctx.send("Unsurprisingly, you're pretty closely related to yourself.")
        await ctx.channel.trigger_typing()

        # Get their relation
        if other is None:
            user, other = ctx.author.id, user
        user_tree = utils.FamilyTreeMember.get(user, ctx.family_guild_id)
        other_tree = utils.FamilyTreeMember.get(other, ctx.family_guild_id)
        async with ctx.channel.typing():
            relation = user_tree.get_relation(other_tree)

        # Get names
        user_name = await self.bot.get_name(user)
        other_name = await self.bot.get_name(other)

        # Output
        if relation is None:
            return await ctx.send(f"`{user_name}` is not related to `{other_name}`.")
        await ctx.send(f"`{other_name}` is `{user_name}`'s {relation}.")

    @commands.command(aliases=['treesize', 'fs', 'ts'], cls=utils.Command)
    @utils.cooldown.cooldown(1, 5, commands.BucketType.user)
    @utils.checks.bot_is_ready()
    @commands.bot_has_permissions(send_messages=True)
    async def familysize(self, ctx:utils.Context, user:utils.converters.UserID=None):
        """Gives you the size of your family tree"""

        # Get user info
        user = user or ctx.author.id
        user_tree = utils.FamilyTreeMember.get(user, ctx.family_guild_id)

        # Get size
        async with ctx.channel.typing():
            size = user_tree.family_member_count

        # Output
        username = await self.bot.get_name(user)
        await ctx.send(f"There are `{size}` people in `{username}`'s family tree.")

    @commands.command(enabled=False, cls=utils.Command)
    @utils.cooldown.cooldown(1, 5, commands.BucketType.user)
    @utils.checks.bot_is_ready()
    @commands.bot_has_permissions(send_messages=True, attach_files=True)
    async def treefile(self, ctx:utils.Context, root:utils.converters.UserID=None):
        """Gives you the full family tree of a user"""

        root_user_id = root or ctx.author.id
        async with ctx.channel.typing():
            text = await utils.FamilyTreeMember.get(root_user_id, ctx.family_guild_id).generate_gedcom_script(self.bot)
        file_bytes = io.BytesIO(text.encode())
        await ctx.send(file=discord.File(file_bytes, filename=f'tree_of_{root_user_id}.ged'))

    @commands.command(aliases=['tree', 't'], cls=utils.Command)
    @utils.cooldown.cooldown(1, 60, commands.BucketType.user)
    @utils.checks.bot_is_ready()
    @commands.bot_has_permissions(send_messages=True, attach_files=True)
    async def familytree(self, ctx:utils.Context, root:utils.converters.UserID=None):
        """Gets the family tree of a given user"""

        try:
            return await self.treemaker(
                ctx=ctx,
                root_user_id=root,
                all_guilds=True,
            )
        except Exception as e:
            raise e

    @commands.command(aliases=['st'], cls=utils.Command)
    @utils.cooldown.cooldown(1, 60, commands.BucketType.user)
    @utils.checks.has_donator_perks("stupidtree_command")
    @utils.checks.bot_is_ready()
    @commands.bot_has_permissions(send_messages=True, attach_files=True)
    async def stupidtree(self, ctx:utils.Context, root:utils.converters.UserID=None):
        """Gets the family tree of a given user"""

        try:
            return await self.treemaker(
                ctx=ctx,
                root_user_id=root,
                stupid_tree=True
            )
        except Exception as e:
            raise e

    async def treemaker(self, ctx:utils.Context, root_user_id:int, all_guilds:bool=False, stupid_tree:bool=False):
        """Handles the generation and sending of the tree to the user"""

        # Get their family tree
        root_user_id = root_user_id or ctx.author.id
        tree = utils.FamilyTreeMember.get(root_user_id, ctx.family_guild_id)

        # Make sure they have one
        if tree.is_empty:
            username = await self.bot.get_name(root_user_id)
            return await ctx.send(f"`{username}` has no family to put into a tree .-.")

        # Write their treemaker code to a file
        start_time = dt.utcnow()
        async with self.bot.database() as db:
            ctu = await utils.CustomisedTreeUser.get(ctx.author.id, db)
        customisation_found_time = dt.utcnow()
        async with ctx.channel.typing():
            if stupid_tree:
                dot_code = await tree.to_full_dot_script(self.bot, ctu)
            else:
                dot_code = await tree.to_dot_script(self.bot, None if all_guilds else ctx.guild, ctu)
        dot_generated_time = dt.utcnow()

        try:
            with open(f'{self.bot.config["tree_file_location"]}/{ctx.author.id}.gz', 'w', encoding='utf-8') as a:
                a.write(dot_code)
        except Exception as e:
            self.logger.error(f"Could not write to {self.bot.config['tree_file_location']}/{ctx.author.id}.gz")
            raise e
        written_to_file_time = dt.utcnow()

        # Convert to an image
        dot = await asyncio.create_subprocess_exec(*[
            'dot',
            '-Tpng:gd',
            f'{self.bot.config["tree_file_location"].rstrip("/")}/{ctx.author.id}.gz',
            '-o',
            f'{self.bot.config["tree_file_location"].rstrip("/")}/{ctx.author.id}.png',
            '-Gcharset=UTF-8',
        ], loop=self.bot.loop)
        await asyncio.wait_for(dot.wait(), 10.0, loop=self.bot.loop)

        # Kill subprocess
        try:
            dot.kill()
        except ProcessLookupError:
            pass  # It already died
        except Exception as e:
            raise e

        # Get time taken
        output_as_image_time = dt.utcnow()
        time_taken = (output_as_image_time - start_time).total_seconds()

        # Generate debug string
        output_string = [
            f"Time taken to get customisations: {(customisation_found_time - start_time).total_seconds() * 1000:.2f}ms",
            f"Time taken to generate dot: {(dot_generated_time - customisation_found_time).total_seconds() * 1000:.2f}ms",
            f"Time taken to write to file: {(written_to_file_time - dot_generated_time).total_seconds() * 1000:.2f}ms",
            f"Time taken to interpret dot: {(output_as_image_time - written_to_file_time).total_seconds() * 1000:.2f}ms",
            f"**Total time taken: {(dt.utcnow() - start_time).total_seconds() * 1000:.2f}ms**",
        ]

        # Send file and delete cached
        file = discord.File(fp=f'{self.bot.config["tree_file_location"]}/{ctx.author.id}.png')
        text = f"[Click here](https://marriagebot.xyz/) to customise your tree. Generated in `{time_taken:.2f}` seconds from `{len(dot_code)}` bytes of DOT code, "
        if stupid_tree:
            text += f"showing {len(tree.span(expand_upwards=True, add_parent=True))} family members."
        else:
            text += f"showing {len(tree.span())} blood relatives out of {len(tree.span(expand_upwards=True, add_parent=True))} total family members (see `{ctx.prefix}perks` for your full family)."
        if ctx.original_author_id in self.bot.owner_ids:
            text += '\n\n' + '\n'.join(output_string)
        await ctx.send(text, file=file)


def setup(bot:utils.Bot):
    x = Information(bot)
    bot.add_cog(x)
