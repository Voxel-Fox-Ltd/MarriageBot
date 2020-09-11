from datetime import datetime as dt

import asyncpg
from discord.ext import commands

from cogs import utils


class ModeratorOnly(utils.Cog):

    @commands.command(cls=utils.Command, hidden=True)
    @utils.checks.is_bot_support()
    @commands.bot_has_permissions(send_messages=True)
    async def uncache(self, ctx:utils.Context, user:utils.converters.UserID):
        """Removes a user from the propsal cache."""

        await self.bot.proposal_cache.remove(user)
        await ctx.send("Sent Redis request to remove user from cache.")

    @commands.command(cls=utils.Command, hidden=True)
    @commands.bot_has_permissions(send_messages=True)
    @utils.cooldown.cooldown(1, 15, commands.BucketType.user)
    async def cachename(self, ctx:utils.Context, user:utils.converters.UserID=None):
        """Removes a user from the propsal cache."""

        user = ctx.author.id or user
        user = await self.bot.fetch_user(user)
        async with self.bot.redis() as re:
            await re.set(f'UserName-{user.id}', str(user))
        self.bot.shallow_users.pop(user.id, None)
        await ctx.send(f"Saved the name `{user!s}` into the database for user ID `{user.id}`.")

    @commands.command(cls=utils.Command)
    @utils.checks.is_bot_support()
    @commands.bot_has_permissions(send_messages=True)
    async def copyfamilytoguild(self, ctx:utils.Context, user:utils.converters.UserID, guild_id:int):
        """Copies a family's span to a given guild ID for server specific families"""

        # Get their current family
        tree = utils.FamilyTreeMember.get(user)
        users = tree.span(expand_upwards=True, add_parent=True)
        await ctx.channel.trigger_typing()

        # Database it to the new guild
        db = await self.bot.database.get_connection()

        # Delete current guild data
        await db('DELETE FROM marriages WHERE guild_id=$1', guild_id)
        await db('DELETE FROM parents WHERE guild_id=$1', guild_id)

        # Generate new data to copy
        parents = ((i.id, i._parent, guild_id) for i in users if i._parent)
        partners = ((i.id, i._partner, guild_id) for i in users if i._partner)

        # Push to db
        await db.conn.copy_records_to_table('parents', columns=['child_id', 'parent_id', 'guild_id'], records=parents)
        await db.conn.copy_records_to_table('marriages', columns=['user_id', 'partner_id', 'guild_id'], records=partners)

        # Send to user
        await ctx.send(f"Copied over `{len(users)}` users.")
        await db.disconnect()

    @commands.command(cls=utils.Command)
    @utils.checks.is_bot_support()
    @commands.bot_has_permissions(send_messages=True)
    async def copyfamilytoguildnodelete(self, ctx:utils.Context, user:utils.converters.UserID, guild_id:int):
        """Copies a family's span to a given guild ID for server specific families"""

        # Get their current family
        tree = utils.FamilyTreeMember.get(user)
        users = tree.span(expand_upwards=True, add_parent=True)
        await ctx.channel.trigger_typing()

        # Database it to the new guild
        db = await self.bot.database.get_connection()

        # Generate new data to copy
        parents = ((i.id, i._parent, guild_id) for i in users if i._parent)
        partners = ((i.id, i._partner, guild_id) for i in users if i._partner)

        # Push to db
        try:
            await db.conn.copy_records_to_table('parents', columns=['child_id', 'parent_id', 'guild_id'], records=parents)
            await db.conn.copy_records_to_table('marriages', columns=['user_id', 'partner_id', 'guild_id'], records=partners)
        except Exception:
            await ctx.send("I encountered an error copying that family over.")
            return

        # Send to user
        await ctx.send(f"Copied over `{len(users)}` users.")
        await db.disconnect()

    @commands.command(cls=utils.Command)
    @utils.checks.is_bot_support()
    @commands.bot_has_permissions(send_messages=True)
    async def addserverspecific(self, ctx:utils.Context, guild_id:int, user_id:utils.converters.UserID):
        """Adds a guild to the MarriageBot Gold whitelist"""

        async with self.bot.database() as db:
            await db('INSERT INTO guild_specific_families (guild_id, purchased_by) VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET purchased_by=excluded.purchased_by', guild_id, user_id)
        await ctx.okay(ignore_error=True)

    @commands.command(cls=utils.Command)
    @utils.checks.is_bot_support()
    @commands.bot_has_permissions(send_messages=True)
    async def removeserverspecific(self, ctx:utils.Context, guild_id:int):
        """Remove a guild from the MarriageBot Gold whitelist"""

        async with self.bot.database() as db:
            await db('DELETE FROM guild_specific_families WHERE guild_id=$1', guild_id)
        await ctx.okay(ignore_error=True)

    @commands.command(cls=utils.Command, aliases=['getgoldpurchases'])
    @utils.checks.is_bot_support()
    @commands.bot_has_permissions(send_messages=True)
    async def getgoldpurchase(self, ctx:utils.Context, user:utils.converters.UserID):
        """Remove a guild from the MarriageBot Gold whitelist"""

        async with self.bot.database() as db:
            rows = await db('SELECT * FROM guild_specific_families WHERE purchased_by=$1', user)
        if not rows:
            return await ctx.send("That user has purchased no instances of MarriageBot Gold.")
        return await ctx.invoke(self.bot.get_command("runsql"), content="SELECT * FROM guild_specific_families WHERE purchased_by={}".format(user))

    @commands.command(cls=utils.Command, hidden=True)
    @utils.checks.is_bot_support()
    @commands.bot_has_permissions(send_messages=True)
    async def recache(self, ctx:utils.Context, user:utils.converters.UserID, guild_id:int=0):
        """Recaches a user's family tree member object"""

        # Read data from DB
        async with self.bot.database() as db:
            parent = await db('SELECT parent_id FROM parents WHERE child_id=$1 AND guild_id=$2', user, guild_id)
            children = await db('SELECT child_id FROM parents WHERE parent_id=$1 AND guild_id=$2', user, guild_id)
            partner = await db('SELECT partner_id FROM marriages WHERE user_id=$1 AND guild_id=$2', user, guild_id)

        # Load data into cache
        children = [i['child_id'] for i in children]
        parent_id = parent[0]['parent_id'] if len(parent) > 0 else None
        partner_id = partner[0]['partner_id'] if len(partner) > 0 else None
        f = utils.FamilyTreeMember(
            user,
            children=children,
            parent_id=parent_id,
            partner_id=partner_id,
            guild_id=guild_id,
        )

        # Push update via redis
        async with self.bot.redis() as re:
            await re.publish_json('TreeMemberUpdate', f.to_json())

        # Output to user
        await ctx.send("Published update for user.")

    @commands.command(cls=utils.Command, hidden=True)
    @utils.checks.is_bot_support()
    @commands.bot_has_permissions(send_messages=True)
    async def recachefamily(self, ctx:utils.Context, user:utils.converters.UserID, guild_id:int=0):
        """Recaches a user's family tree member object, but through their whole family"""

        # Get connections
        db = await self.bot.database.get_connection()
        re = await self.bot.redis.get_connection()

        # Loop through their tree
        family = utils.FamilyTreeMember.get(user, guild_id).span(expand_upwards=True, add_parent=True)[:]
        for i in family:
            parent = await db('SELECT parent_id FROM parents WHERE child_id=$1 AND guild_id=$2', i.id, guild_id)
            children = await db('SELECT child_id FROM parents WHERE parent_id=$1 AND guild_id=$2', i.id, guild_id)
            partner = await db('SELECT partner_id FROM marriages WHERE user_id=$1 AND guild_id=$2', i.id, guild_id)

            # Load data into cache
            children = [i['child_id'] for i in children]
            parent_id = parent[0]['parent_id'] if len(parent) > 0 else None
            partner_id = partner[0]['partner_id'] if len(partner) > 0 else None
            f = utils.FamilyTreeMember(
                i.id,
                children=children,
                parent_id=parent_id,
                partner_id=partner_id,
                guild_id=guild_id,
            )

            # Push update via redis
            await re.publish_json('TreeMemberUpdate', f.to_json())

        # Disconnect from database
        await db.disconnect()
        await re.disconnect()

        # Output to user
        await ctx.send(f"Published `{len(family)}` updates.")

    @commands.command(cls=utils.Command)
    @utils.checks.is_server_specific_bot_moderator()
    @commands.bot_has_permissions(send_messages=True)
    async def forcemarry(self, ctx:utils.Context, user_a:utils.converters.UserID, user_b:utils.converters.UserID=None):
        """Marries the two specified users"""

        # Correct params
        if user_b is None:
            user_a, user_b = ctx.author.id, user_a
        if user_a == user_b:
            return await ctx.send("You can't marry yourself.")

        # Get users
        me = utils.FamilyTreeMember.get(user_a, ctx.family_guild_id)
        them = utils.FamilyTreeMember.get(user_b, ctx.family_guild_id)

        # See if they have partners
        if me.partner is not None:
            return await ctx.send(f"<@{me.id}> already has a partner.")
        if them.partner is not None:
            return await ctx.send(f"<@{them.id}> already has a partner.")

        # Update database
        async with self.bot.database() as db:
            await db.marry(user_a, user_b, ctx.family_guild_id)
        me._partner = user_b
        them._partner = user_a
        async with self.bot.redis() as re:
            await re.publish_json('TreeMemberUpdate', me.to_json())
            await re.publish_json('TreeMemberUpdate', them.to_json())
        await ctx.send(f"Married <@{me.id}> and <@{them.id}>.")

    @commands.command(cls=utils.Command)
    @utils.checks.is_server_specific_bot_moderator()
    @commands.bot_has_permissions(send_messages=True)
    async def forcedivorce(self, ctx:utils.Context, user:utils.converters.UserID):
        """Divorces a user from their spouse"""

        # Get user
        me = utils.FamilyTreeMember.get(user, ctx.family_guild_id)
        if not me.partner:
            return await ctx.send(f"<@{me.id}> isn't even married .-.")

        # Update database
        async with self.bot.database() as db:
            await db('DELETE FROM marriages WHERE (user_id=$1 OR partner_id=$1) AND guild_id=$2', user, ctx.family_guild_id)

        # Update cache
        me.partner._partner = None
        them = me.partner
        me._partner = None
        async with self.bot.redis() as re:
            await re.publish_json('TreeMemberUpdate', me.to_json())
            await re.publish_json('TreeMemberUpdate', them.to_json())
        await ctx.send("Consider it done.")

    @commands.command(cls=utils.Command)
    @utils.checks.is_server_specific_bot_moderator()
    @commands.bot_has_permissions(send_messages=True)
    async def forceadopt(self, ctx:utils.Context, parent:utils.converters.UserID, child:utils.converters.UserID=None):
        """Adds the child to the specified parent"""

        # Correct params
        if child is None:
            parent, child = ctx.author.id, parent

        # Check users
        them = utils.FamilyTreeMember.get(child, ctx.family_guild_id)
        child_name = await self.bot.get_name(child)
        if them.parent:
            return await ctx.send(f"`{child_name!s}` already has a parent.")

        # Update database
        async with self.bot.database() as db:
            await db('INSERT INTO parents (parent_id, child_id, guild_id, timestamp) VALUES ($1, $2, $3, $4)', parent, child, ctx.family_guild_id, dt.utcnow())

        # Update cache
        me = utils.FamilyTreeMember.get(parent, ctx.family_guild_id)
        me._children.append(child)
        them._parent = parent
        async with self.bot.redis() as re:
            await re.publish_json('TreeMemberUpdate', me.to_json())
            await re.publish_json('TreeMemberUpdate', them.to_json())
        await ctx.send(f"Added <@{child}> to <@{parent}>'s children list.")

    @commands.command(aliases=['forceeman'], cls=utils.Command)
    @utils.checks.is_server_specific_bot_moderator()
    @commands.bot_has_permissions(send_messages=True)
    async def forceemancipate(self, ctx:utils.Context, user:utils.converters.UserID):
        """Force emancipates a child"""

        # Run checks
        me = utils.FamilyTreeMember.get(user, ctx.family_guild_id)
        if not me.parent:
            return await ctx.send(f"<@{me.id}> doesn't even have a parent .-.")

        # Update database
        async with self.bot.database() as db:
            await db('DELETE FROM parents WHERE child_id=$1 AND guild_id=$2', me.id, me._guild_id)

        # Update cache
        me.parent._children.remove(user)
        parent = me.parent
        me._parent = None
        async with self.bot.redis() as re:
            await re.publish_json('TreeMemberUpdate', me.to_json())
            await re.publish_json('TreeMemberUpdate', parent.to_json())
        await ctx.send("Consider it done.")

    @commands.command(cls=utils.Command, hidden=True)
    @utils.checks.is_bot_support()
    @commands.bot_has_permissions(send_messages=True)
    async def addvoter(self, ctx:utils.Context, user:utils.converters.UserID):
        """Adds a voter to the database"""

        self.bot.dbl_votes[user] = dt.now()
        async with self.bot.database() as db:
            await db('INSERT INTO dbl_votes (user_id, timestamp) VALUES ($1, $2) ON CONFLICT (user_id) DO UPDATE SET timestamp=$2', user, self.bot.dbl_votes[user])
        await ctx.send("Consider it done.")

    @commands.command(aliases=['addblogpost'], cls=utils.Command, hidden=True)
    @utils.checks.is_bot_support()
    @commands.bot_has_permissions(send_messages=True)
    async def createblogpost(self, ctx:utils.Context, url:str, title:str, *, content:str=None):
        """Adds a blog post to the database"""

        if content is None:
            return await ctx.send("You can't send no content.")
        verb = "Created"
        async with self.bot.database() as db:
            try:
                await db("INSERT INTO blog_posts VALUES ($1, $2, $3, NOW(), $4)", url, title, content, ctx.author.id)
            except asyncpg.UniqueViolationError:
                await db("UPDATE blog_posts SET url=$1, title=$2, body=$3, created_at=NOW(), author_id=$4 WHERE url=$1", url, title, content, ctx.author.id)
                verb = "Updated"
        await ctx.send(f"{verb} blog post: https://marriagebot.xyz/blog/{url}", embeddify=False)

    @commands.command(cls=utils.Command, hidden=True)
    @utils.checks.is_bot_support()
    @commands.bot_has_permissions(send_messages=True)
    async def createredirect(self, ctx:utils.Context, code:str, redirect:str):
        """Adds a redirect to the database"""

        async with self.bot.database() as db:
            await db("INSERT INTO redirects VALUES ($1, $2)", code, redirect)
        await ctx.send(f"Created redirect: https://marriagebot.xyz/r/{code}", embeddify=False)


def setup(bot:utils.Bot):
    x = ModeratorOnly(bot)
    bot.add_cog(x)
