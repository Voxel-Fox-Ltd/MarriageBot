import os
import asyncio
from datetime import datetime as dt, timedelta

import psutil
import discord
from discord.ext import commands

from cogs import utils


class Misc(utils.Cog):

    def __init__(self, bot:utils.CustomBot):
        super().__init__(bot)
        self.process = psutil.Process(os.getpid())
        self.process.cpu_percent()

    @commands.command(aliases=['upvote'])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def vote(self, ctx:utils.Context):
        """Gives you a link to upvote the bot on DiscordBotList"""

        if self.bot.config['dbl_vainity']:
            url = f"https://discordbots.org/bot/{self.bot.config['dbl_vainity']}/vote"
        else:
            url = f"https://discordbots.org/bot/{self.bot.user.id}/vote"
        await ctx.send(f"[Add a DBL vote]({url})!\nSee `{ctx.clean_prefix}perks` for more information.")

    @commands.command(aliases=['git', 'code'])
    @commands.cooldown(1, 5, commands.BucketType.user)
    @utils.checks.has_set_config('github')
    async def github(self, ctx:utils.Context):
        """Gives you a link to the bot's code repository"""

        await ctx.send(f"<{self.bot.config['github']}>", embeddify=False)

    @commands.command(aliases=['patreon', 'paypal'])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def donate(self, ctx:utils.Context):
        """Gives you the creator's donation links"""

        links = []
        if self.bot.config['patreon']:
            links.append(f"Patreon: <{self.bot.config['patreon']}> (see {ctx.prefix}perks to see what you get)")
        if self.bot.config['paypal']:
            links.append(f"PayPal: <{self.bot.config['paypal']}> (doesn't get you the perks, but is very appreciated)")
        if not links:
            raise utils.errors.NoSetConfig([])
        await ctx.send('\n'.join(links), embeddify=False)

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def invite(self, ctx:utils.Context):
        """Gives you an invite link for the bot"""

        await ctx.send(f"<{self.bot.invite_link}>", embeddify=False)

    @commands.command(aliases=['guild', 'support'])
    @commands.cooldown(1, 5, commands.BucketType.user)
    @utils.checks.has_set_config('guild_invite')
    async def server(self, ctx:utils.Context):
        """Gives you a server invite link"""

        await ctx.send(self.bot.config['guild_invite'], embeddify=False)

    @commands.command(hidden=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def echo(self, ctx:utils.Context, *, content:str):
        """Echos a saying"""

        await ctx.send(content, embeddify=False)

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def perks(self, ctx:utils.Context):
        """Shows you the perks associated with different support tiers"""

        # Normies
        normal_users = [
            "60s tree cooldown",
            "5 children",
        ]

        # Perks for voting
        voting_perks = [
            "Previous tiers' perks",
            "30s tree cooldown",
        ]

        # Perks for $1 Patrons
        t1_donate_perks = [
            "Previous tiers' perks",
            "15s tree cooldown",
            "Up to 10 children",
            "`disownall` command (disowns all of your children at once)",
        ]

        # $3 Patrons
        t2_donate_perks = [
            "Previous tiers' perks",
            "Up to 15 children",
            "`stupidtree` command (shows all relations, not just blood relatives)",
        ]

        # Perks for $5 Patrons
        t3_donate_perks = [
            "Previous tiers' perks",
            "5s tree cooldown",
            "Up to 20 children",
        ]

        # Perks for MarriageBot Gold
        gold_perks = [
            "5s tree cooldown for all users",
            "Togglable incest",
            "Faster bot responses",
            "Server specific families",
            "Access to the `forcemarry`, `forcedivorce`, and `forceemancipate` commands"
        ]
        e = discord.Embed()
        e.add_field(name=f'Normal Users', value=f"Gives you access to:\n* " + '\n* '.join(normal_users), inline=False)
        e.add_field(name=f'Voting ({ctx.clean_prefix}vote)', value=f"Gives you access to:\n* " + '\n* '.join(voting_perks), inline=False)
        e.add_field(name=f'T1 Patreon Donation ({ctx.clean_prefix}donate)', value=f"Gives you access to:\n* " + '\n* '.join(t1_donate_perks), inline=False)
        e.add_field(name=f'T2 Patreon Donation ({ctx.clean_prefix}donate)', value=f"Gives you access to:\n* " + '\n* '.join(t2_donate_perks), inline=False)
        e.add_field(name=f'T3 Patreon Donation ({ctx.clean_prefix}donate)', value=f"Gives you access to:\n* " + '\n* '.join(t3_donate_perks), inline=False)
        e.add_field(name=f'MarriageBot Gold ({ctx.clean_prefix}ssf)', value=f"Gvies you access to:\n* " + '\n* '.join(gold_perks), inline=False)
        await ctx.send(embed=e)


    @commands.command(aliases=['status'])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def stats(self, ctx:utils.Context):
        """Gives you the stats for the bot"""

        # await ctx.channel.trigger_typing()
        embed = discord.Embed(
            colour=0x1e90ff
        )
        embed.set_footer(text=str(self.bot.user), icon_url=self.bot.user.avatar_url)
        embed.add_field(name="MarriageBot", value="A robot for marrying your friends and adopting your enemies.")
        creator_id = self.bot.config["owners"][0]
        creator = await self.bot.get_name(creator_id)
        embed.add_field(name="Creator", value=f"{creator}\n{creator_id}")
        embed.add_field(name="Library", value=f"Discord.py {discord.__version__}")
        embed.add_field(name="Average Guild Count", value=int((len(self.bot.guilds) / len(self.bot.shard_ids)) * self.bot.shard_count))
        embed.add_field(name="Shard Count", value=self.bot.shard_count)
        embed.add_field(name="Average WS Latency", value=f"{(self.bot.latency * 1000):.2f}ms")
        embed.add_field(name="Coroutines", value=f"{len([i for i in asyncio.Task.all_tasks() if not i.done()])} running, {len(asyncio.Task.all_tasks())} total.")
        embed.add_field(name="Process ID", value=self.process.pid)
        embed.add_field(name="CPU Usage", value=f"{self.process.cpu_percent():.2f}")
        embed.add_field(name="Memory Usage", value=f"{self.process.memory_info()[0]/2**20:.2f}MB/{psutil.virtual_memory()[0]/2**20:.2f}MB")
        ut = self.bot.get_uptime()  # Uptime
        uptime = [
            int(ut // (60*60*24)),
            int((ut % (60*60*24)) // (60*60)),
            int(((ut % (60*60*24)) % (60*60)) // 60),
            ((ut % (60*60*24)) % (60*60)) % 60,
        ]
        embed.add_field(name="Uptime", value=f"{uptime[0]} days, {uptime[1]} hours, {uptime[2]} minutes, and {uptime[3]:.2f} seconds.")
        # embed.add_field(name="Family Members", value=len(FamilyTreeMember.all_users) - 1)
        try:
            await ctx.send(embed=embed)
        except Exception:
            await ctx.send("I tried to send an embed, but I couldn't.")

    @commands.command(aliases=['clean'])
    async def clear(self, ctx:utils.Context):
        """Clears the bot's commands from chat"""

        if ctx.channel.permissions_for(ctx.guild.me).manage_messages:
            _ = await ctx.channel.purge(limit=100, check=lambda m: m.author.id == self.bot.user.id)
        else:
            _ = await ctx.channel.purge(limit=100, check=lambda m: m.author.id == self.bot.user.id, bulk=False)
        await ctx.send(f"Cleared `{len(_)}` messages from chat.", delete_after=3.0)

    @commands.command()
    async def block(self, ctx:utils.Context, user_id:utils.converters.UserID):
        """Blocks a user from being able to adopt/makeparent/whatever you"""

        # Get current blocks
        current_blocks = self.bot.blocked_users.get(ctx.author.id, list())
        if user_id in current_blocks:
            await ctx.send("That user is already blocked.")
            return

        # Add to list
        async with self.bot.database() as db:
            await db(
                'INSERT INTO blocked_user (user_id, blocked_user_id) VALUES ($1, $2)',
                ctx.author.id, user_id
            )
        async with self.bot.redis() as re:
            await re.publish_json("BlockedUserAdd", {"user_id": ctx.author.id, "blocked_user_id": user_id})

        # Tell user
        await ctx.send("That user is now blocked.")

    @commands.command()
    async def unblock(self, ctx:utils.Context, user:utils.converters.UserID):
        """Unblocks a user and allows them to adopt/makeparent/whatever you"""

        # Get current blocks
        current_blocks = self.bot.blocked_users[ctx.author.id]
        if user not in current_blocks:
            await ctx.send("You don't have that user blocked.")
            return

        # Remove from list
        async with self.bot.database() as db:
            await db(
                'DELETE FROM blocked_user WHERE user_id=$1 AND blocked_user_id=$2',
                ctx.author.id, user
            )
        async with self.bot.redis() as re:
            await re.publish_json("BlockedUserRemove", {"user_id": ctx.author.id, "blocked_user_id": user_id})

        # Tell user
        await ctx.send("That user is now unblocked.")

    @commands.command()
    async def shard(self, ctx:utils.Context):
        """Gives you the shard that your server is running on"""

        await ctx.send(f"The shard that your server is on is shard `{ctx.guild.shard_id}`.")


def setup(bot:utils.CustomBot):
    x = Misc(bot)
    bot.add_cog(x)
