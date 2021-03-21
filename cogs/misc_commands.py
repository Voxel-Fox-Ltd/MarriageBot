import discord
from discord.ext import commands
import voxelbotutils as utils


class MiscCommands(utils.Cog):
    """
    Misc commands, pretty much just stuff that VBU doesnt handle and doesnt go into any other category.
    """

    @utils.command()
    @utils.cooldown.cooldown(1, 5, commands.BucketType.user, cls=utils.cooldown.NoRaiseCooldown)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    @utils.checks.is_config_set('command_data', 'stats_command_enabled')
    async def perks(self, ctx:utils.Context):
        """
        Shows you the perks associated with different support tiers.
        """

        # Normies
        normal_users = [
            "60s tree cooldown",
            "5 children",
        ]

        # Perks for voting
        voting_perks = [
            "30s tree cooldown",
            "5 children",
        ]

        # The Nitro perks would go here but I want to keep them mostly undocumented

        # Perks for $1 Patrons
        t1_donate_perks = [
            "15s tree cooldown",
            "10 children",
            "`disownall` command (disowns all of your children at once)",
        ]

        # $3 Patrons
        t2_donate_perks = [
            "15s tree cooldown",
            "15 children",
            "`disownall` command (disowns all of your children at once)",
            "`stupidtree` command (shows all relations, not just blood relatives)",
        ]

        # Perks for $5 Patrons
        t3_donate_perks = [
            "5s tree cooldown",
            "20 children",
            "`disownall` command (disowns all of your children at once)",
            "`stupidtree` command (shows all relations, not just blood relatives)",
        ]

        # Perks for MarriageBot Gold
        gold_perks = [
            "5s tree cooldown for all users",
            "Togglable incest",
            "Server specific families",
            "Access to the `forcemarry`, `forcedivorce`, and `forceemancipate` commands",
            f"Maximum 2000 family members (as opposed to the normal {self.bot.config['max_family_members']})",
            "Configurable maximum children per role",
        ]

        # Make embed
        e = discord.Embed()
        e.add_field(name='Normal Users', value="Gives you access to:\n* " + '\n* '.join(normal_users), inline=False)
        e.add_field(name=f'Voting ({ctx.prefix}vote)', value="Gives you access to:\n* " + '\n* '.join(voting_perks), inline=False)
        e.add_field(name=f'T1 Subscriber ({ctx.prefix}donate)', value="Gives you access to:\n* " + '\n* '.join(t1_donate_perks), inline=False)
        e.add_field(name=f'T2 Subscriber ({ctx.prefix}donate)', value="Gives you access to:\n* " + '\n* '.join(t2_donate_perks), inline=False)
        e.add_field(name=f'T3 Subscriber ({ctx.prefix}donate)', value="Gives you access to:\n* " + '\n* '.join(t3_donate_perks), inline=False)
        e.add_field(name=f'MarriageBot Gold ({ctx.prefix}gold)', value="Gives you access to:\n* " + '\n* '.join(gold_perks), inline=False)
        await ctx.send(embed=e)

    @utils.command()
    @commands.bot_has_permissions(send_messages=True)
    async def block(self, ctx:utils.Context, user_id:utils.converters.UserID):
        """
        Blocks a user from being able to adopt/makeparent/whatever you.
        """

        # Get current blocks
        current_blocks = self.bot.blocked_users.get(ctx.author.id, list())
        if user_id in current_blocks:
            return await ctx.send("That user is already blocked.")

        # Add to list
        async with self.bot.database() as db:
            await db(
                'INSERT INTO blocked_user (user_id, blocked_user_id) VALUES ($1, $2)',
                ctx.author.id, user_id
            )
        async with self.bot.redis() as re:
            await re.publish_json("BlockedUserAdd", {"user_id": ctx.author.id, "blocked_user_id": user_id})
        return await ctx.send("That user is now blocked.")

    @utils.command()
    @commands.bot_has_permissions(send_messages=True)
    async def unblock(self, ctx:utils.Context, user:utils.converters.UserID):
        """
        Unblocks a user and allows them to adopt/makeparent/whatever you.
        """

        # Get current blocks
        current_blocks = self.bot.blocked_users[ctx.author.id]
        if user not in current_blocks:
            return await ctx.send("You don't have that user blocked.")

        # Remove from list
        async with self.bot.database() as db:
            await db(
                'DELETE FROM blocked_user WHERE user_id=$1 AND blocked_user_id=$2',
                ctx.author.id, user
            )
        async with self.bot.redis() as re:
            await re.publish_json("BlockedUserRemove", {"user_id": ctx.author.id, "blocked_user_id": user})
        return await ctx.send("That user is now unblocked.")

    @utils.command()
    @commands.guild_only()
    @commands.bot_has_permissions(send_messages=True)
    async def shard(self, ctx:utils.Context, guild_id:int=None):
        """
        Gives you the shard that your server is running on.
        """

        guild_id = guild_id or ctx.guild.id
        await ctx.send(
            f"The shard for server ID `{guild_id}` is `{(guild_id >> 22) % self.bot.shard_count}`. "
            f"If all instances have `{len(self.bot.shard_ids)}` shards, that guild would be on instance "
            f"`{((guild_id >> 22) % self.bot.shard_count) // len(self.bot.shard_ids)}`."
        )


def setup(bot:utils.Bot):
    x = MiscCommands(bot)
    bot.add_cog(x)
