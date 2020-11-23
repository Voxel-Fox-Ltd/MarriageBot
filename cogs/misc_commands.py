import asyncio
import os

import discord
import psutil
from discord.ext import commands

from cogs import utils


class MiscCommands(utils.Cog):

    def __init__(self, bot:utils.Bot):
        super().__init__(bot)
        self.process = psutil.Process(os.getpid())
        self.process.cpu_percent()

    @commands.command(aliases=['upvote'], cls=utils.Command)
    @utils.cooldown.cooldown(1, 5, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    async def vote(self, ctx:utils.Context):
        """Gives you a link to upvote the bot on DiscordBotList"""

        url = f"https://discordbots.org/bot/{self.bot.config.get('dbl_vainity', None) or self.bot.user.id}/vote"
        await ctx.send(f"[Add a DBL vote]({url})!\nSee `m!perks` for more information.")

    @commands.command(aliases=['git', 'code'], cls=utils.Command)
    @utils.cooldown.cooldown(1, 5, commands.BucketType.user)
    @utils.checks.is_config_set('command_data', 'github')
    @commands.bot_has_permissions(send_messages=True)
    async def github(self, ctx:utils.Context):
        """Gives you a link to the bot's code repository"""

        await ctx.send(f"<{self.bot.config['command_data']['github']}>", embeddify=False)

    @commands.command(aliases=['patreon'], cls=utils.Command)
    @utils.cooldown.cooldown(1, 5, commands.BucketType.user)
    @utils.checks.is_config_set('command_data', 'patreon')
    @commands.bot_has_permissions(send_messages=True)
    async def donate(self, ctx:utils.Context):
        """Gives you the creator's donation links"""

        await ctx.send(f"See `{ctx.prefix}perks` for more information!\n<{self.bot.config['command_data']['patreon']}>", embeddify=False)

    @commands.command(cls=utils.Command)
    @utils.cooldown.cooldown(1, 5, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
    @utils.checks.is_config_set('command_data', 'invite_command_enabled')
    async def invite(self, ctx:utils.Context):
        """Gives you an invite link for the bot"""

        await ctx.send(f"<{self.bot.get_invite_link(embed_links=True, attach_files=True)}>", embeddify=False)

    @commands.command(aliases=['guild', 'support'], cls=utils.Command)
    @utils.cooldown.cooldown(1, 5, commands.BucketType.user)
    @utils.checks.is_config_set('command_data', 'guild_invite')
    @commands.bot_has_permissions(send_messages=True)
    async def server(self, ctx:utils.Context):
        """Gives you a server invite link"""

        await ctx.send(self.bot.config['command_data']['guild_invite'], embeddify=False)

    @commands.command(hidden=True, cls=utils.Command)
    @utils.cooldown.cooldown(1, 5, commands.BucketType.user)
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(send_messages=True)
    @utils.checks.is_config_set('command_data', 'echo_command_enabled')
    async def echo(self, ctx:utils.Context, *, content:str):
        """Echos the given content into the channel"""

        await ctx.send(content, embeddify=False)

    @commands.command(cls=utils.Command)
    @utils.cooldown.cooldown(1, 5, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    @utils.checks.is_config_set('command_data', 'stats_command_enabled')
    async def perks(self, ctx:utils.Context):
        """Shows you the perks associated with different support tiers"""

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

    @commands.command(aliases=['status','botinfo'], cls=utils.Command)
    @utils.cooldown.cooldown(1, 5, commands.BucketType.user)
    @commands.bot_has_permissions(send_messages=True)
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
            int(ut // (60 * 60 * 24)),
            int((ut % (60 * 60 * 24)) // (60 * 60)),
            int(((ut % (60 * 60 * 24)) % (60 * 60)) // 60),
            ((ut % (60 * 60 * 24)) % (60 * 60)) % 60,
        ]
        embed.add_field(name="Uptime", value=f"{uptime[0]} days, {uptime[1]} hours, {uptime[2]} minutes, and {uptime[3]:.2f} seconds.")
        # embed.add_field(name="Family Members", value=len(FamilyTreeMember.all_users) - 1)
        try:
            await ctx.send(embed=embed)
        except Exception:
            await ctx.send("I tried to send an embed, but I couldn't.")

    @commands.command(aliases=['clean'], cls=utils.Command)
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    @commands.bot_has_permissions(send_messages=True)
    async def clear(self, ctx:utils.Context):
        """Clears the bot's commands from chat"""

        if ctx.channel.permissions_for(ctx.guild.me).manage_messages:
            _ = await ctx.channel.purge(limit=100, check=lambda m: m.author.id == self.bot.user.id)
        else:
            _ = await ctx.channel.purge(limit=100, check=lambda m: m.author.id == self.bot.user.id, bulk=False)
        await ctx.send(f"Cleared `{len(_)}` messages from chat.", delete_after=3.0)

    @commands.command(cls=utils.Command)
    @commands.bot_has_permissions(send_messages=True)
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

    @commands.command(cls=utils.Command)
    @commands.bot_has_permissions(send_messages=True)
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
            await re.publish_json("BlockedUserRemove", {"user_id": ctx.author.id, "blocked_user_id": user})

        # Tell user
        await ctx.send("That user is now unblocked.")

    @commands.command(cls=utils.Command)
    @commands.guild_only()
    @commands.bot_has_permissions(send_messages=True)
    async def shard(self, ctx:utils.Context, guild_id:int=None):
        """Gives you the shard that your server is running on"""

        guild_id = guild_id or ctx.guild.id
        await ctx.send(f"The shard for server ID `{guild_id}` is `{(guild_id >> 22) % self.bot.shard_count}`. If all instances have `{len(self.bot.shard_ids)}` shards, that guild would be on instance `{((guild_id >> 22) % self.bot.shard_count) // len(self.bot.shard_ids)}`")

    @commands.command(cls=utils.Command, aliases=['kitty'], hidden=True)
    @commands.bot_has_permissions(send_messages=True)
    async def cat(self, ctx:utils.Context):
        """Gives you some cats innit"""

        await ctx.channel.trigger_typing()
        headers = {"User-Agent": "MarriageBot/1.0.0 - Discord@Kae#0004"}
        async with self.bot.session.get("https://api.thecatapi.com/v1/images/search", headers=headers) as r:
            data = await r.json()
        with utils.Embed(use_random_colour=True) as embed:
            embed.set_image(url=data[0]['url'])
        await ctx.send(embed=embed)


def setup(bot:utils.Bot):
    x = MiscCommands(bot)
    bot.add_cog(x)
