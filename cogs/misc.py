from discord.ext import commands

from cogs import utils


class Misc(utils.Cog):

    @commands.command(aliases=['git', 'code'], cls=utils.Command)
    @utils.checks.is_config_set('command_data', 'github')
    async def github(self, ctx:utils.Context):
        """Sends the GitHub Repository link"""

        await ctx.send(f"<{self.bot.config['command_data']['github']}>")

    @commands.command(aliases=['support', 'guild'], cls=utils.Command)
    @utils.checks.is_config_set('command_data', 'guild_invite')
    async def server(self, ctx:utils.Context):
        """Gives the invite to the support server"""

        await ctx.send(f"<{self.bot.config['command_data']['guild_invite']}>")

    @commands.command(aliases=['patreon'], cls=utils.Command)
    @utils.checks.is_config_set('command_data', 'patreon')
    async def donate(self, ctx:utils.Context):
        """Gives you the bot's creator's Patreon"""

        await ctx.send(f"<{self.bot.config['command_data']['patreon']}>")

    @commands.command(cls=utils.Command)
    async def invite(self, ctx:utils.Context):
        """Gives you the bot's invite link"""

        await ctx.send(f"<{self.bot.get_invite_link()}>")

    @commands.command(cls=utils.Command)
    async def echo(self, ctx:utils.Context, *, content:utils.converters.CleanContent):
        """Echos the given content into the channel"""

        await ctx.send(content)
                       
    @command(aliases=['status'])
    @cooldown(1, 5, BucketType.user)
    async def stats(self, ctx:Context):
        '''Gives you the stats for the bot'''       

        # await ctx.channel.trigger_typing()
        embed = Embed(
            colour=0x1e90ff
        )
        embed.set_footer(text=str(self.bot.user), icon_url=self.bot.user.avatar_url)
        embed.add_field(name="ProfileBot", value="A bot to make the process of filling out forms fun.")
        creator_id = self.bot.config["owners"][0]
        creator = await self.bot.fetch_user(creator_id)
        embed.add_field(name="Creator", value=f"{creator!s}\n{creator_id}")
        embed.add_field(name="Library", value=f"Discord.py {dpy_version}")
        try:
            embed.add_field(name="Average Guild Count", value=int((len(self.bot.guilds) / len(self.bot.shard_ids)) * self.bot.shard_count))
        except TypeError:
            embed.add_field(name="Guild Count", value=len(self.bot.guilds))
        embed.add_field(name="Shard Count", value=self.bot.shard_count)
        embed.add_field(name="Average WS Latency", value=f"{(self.bot.latency * 1000):.2f}ms")
        embed.add_field(name="Coroutines", value=f"{len([i for i in Task.all_tasks() if not i.done()])} running, {len(Task.all_tasks())} total.")
        embed.add_field(name="Process ID", value=self.process.pid)
        try:
            await ctx.send(embed=embed)
        except Exception:
            await ctx.send("I tried to send an embed, but I couldn't.")


def setup(bot:utils.Bot):
    x = Misc(bot)
    bot.add_cog(x)
