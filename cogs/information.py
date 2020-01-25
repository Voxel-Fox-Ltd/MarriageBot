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
    async def partner(self, ctx:utils.Context, user:typing.Optional[utils.converters.UserID]):
        """Tells you who a user is married to"""

        # Get the user's info
        user = user or ctx.author.id
        user_name = await self.bot.get_name(user)
        user_info = utils.FamilyTreeMember.get(user, ctx.family_guild_id)

        # Output
        if user_info._partner is None:
            return await ctx.send(f"`{user_name}` is not currently married.")
        partner_name = await self.bot.get_name(user_info._partner)
        async with self.bot.database() as db:
            if self.bot.is_server_specific:
                data = await db("SELECT * FROM marriages WHERE user_id=$1 AND guild_id<>0", ctx.author.id)
            else:
                data = await db("SELECT * FROM marriages WHERE user_id=$1 AND guild_id=0", ctx.author.id)
        timestamp = data[0]['timestamp']
        if timestamp:
            await ctx.send(f"`{user_name}` is currently married to `{partner_name}` (`{user_info._partner}`). They've been married since {timestamp.strftime('%B %d %Y')}.")
        else:
            await ctx.send(f"`{user_name}` is currently married to `{partner_name}` (`{user_info._partner}`).")

    @commands.command(aliases=['child', 'kids'], cls=utils.Command)
    @utils.cooldown.cooldown(1, 5, commands.BucketType.user)
    @utils.checks.bot_is_ready()
    async def children(self, ctx:utils.Context, user:typing.Optional[utils.converters.UserID]):
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
    async def parent(self, ctx:utils.Context, user:typing.Optional[utils.converters.UserID]):
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
    async def relationship(self, ctx:utils.Context, user:utils.converters.UserID, other:typing.Optional[utils.converters.UserID]):
        """Gets the relationship between the two specified users"""

        # Check against themselves
        if (user == ctx.author and other is None) or (user == other):
            return await ctx.send(f"Unsurprisingly, you're pretty closely related to yourself.")
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
    async def familysize(self, ctx:utils.Context, user:typing.Optional[utils.converters.UserID]):
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
    @commands.bot_has_permissions(attach_files=True)
    @utils.checks.bot_is_ready()
    async def treefile(self, ctx:utils.Context, root:typing.Optional[utils.converters.UserID]):
        """Gives you the full family tree of a user"""

        root_user_id = root or ctx.author.id
        async with ctx.channel.typing():
            text = await utils.FamilyTreeMember.get(root_user_id, ctx.family_guild_id).generate_gedcom_script(self.bot)
        file_bytes = io.BytesIO(text.encode())
        await ctx.send(file=discord.File(file_bytes, filename=f'tree_of_{root_user_id}.ged'))

    @commands.command(aliases=['familytree', 't', 'fulltree', 'ft', 'gt'], cls=utils.Command)
    @utils.cooldown.cooldown(1, 60, commands.BucketType.user)
    @commands.bot_has_permissions(attach_files=True)
    @utils.checks.bot_is_ready()
    async def tree(self, ctx:utils.Context, root:typing.Optional[utils.converters.UserID]):
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
    @utils.checks.is_patreon(tier=2)
    @commands.bot_has_permissions(attach_files=True)
    @utils.checks.bot_is_ready()
    async def stupidtree(self, ctx:utils.Context, root:typing.Optional[utils.converters.UserID]):
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
        start_time = dt.now()
        async with self.bot.database() as db:
            ctu = await utils.CustomisedTreeUser.get(ctx.author.id, db)
        async with ctx.channel.typing():
            if stupid_tree:
                dot_code = await tree.to_full_dot_script(self.bot, ctu)
            else:
                dot_code = await tree.to_dot_script(self.bot, None if all_guilds else ctx.guild, ctu)

        try:
            with open(f'{self.bot.config["tree_file_location"]}/{ctx.author.id}.gz', 'w', encoding='utf-8') as a:
                a.write(dot_code)
        except Exception as e:
            self.logger.error(f"Could not write to {self.bot.config['tree_file_location']}/{ctx.author.id}.gz")
            raise e

        # Convert to an image
        dot = await asyncio.create_subprocess_exec(*[
            'dot',
            '-Tpng',
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
        end_time = dt.now()
        time_taken = (end_time - start_time).total_seconds()

        # Send file and delete cached
        file = discord.File(fp=f'{self.bot.config["tree_file_location"]}/{ctx.author.id}.png')
        await ctx.send(f"[Click here](https://marriagebot.xyz/) to customise your tree. Generated in `{time_taken:.2f}` seconds from `{len(dot_code)}` bytes of DOT code.", file=file)


def setup(bot:utils.Bot):
    x = Information(bot)
    bot.add_cog(x)
