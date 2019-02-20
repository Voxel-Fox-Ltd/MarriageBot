from os import getpid
from asyncio import Task
from random import choice
from datetime import datetime as dt, timedelta

from psutil import Process, virtual_memory
from discord import Embed, __version__ as dpy_version
from discord.ext.commands import command, Context
from discord.ext.commands.cooldowns import BucketType

from cogs.utils.custom_bot import CustomBot 
from cogs.utils.checks.cooldown import cooldown
from cogs.utils.family_tree.family_tree_member import FamilyTreeMember


class Misc(object):

    def __init__(self, bot:CustomBot):
        self.bot = bot 
        pid = getpid()
        self.process = Process(pid)
        self.process.cpu_percent()


    @command(aliases=['vote'])
    @cooldown(1, 5, BucketType.user)
    async def upvote(self, ctx:Context):
        '''
        Gives you a link to upvote the bot
        '''

        if self.bot.config['dbl_vainity']:
            await ctx.send(f"<https://discordbots.org/bot/{self.bot.config['dbl_vainity']}/vote>")
        else:
            await ctx.send(f"<https://discordbots.org/bot/{self.bot.user.id}/vote>")


    @command(aliases=['git', 'code'])
    @cooldown(1, 5, BucketType.user)
    async def github(self, ctx:Context):
        '''
        Gives you a link to the bot's code repository
        '''

        await ctx.send(f"<{self.bot.config['github']}>")


    @command(aliases=['patreon', 'paypal'])
    @cooldown(1, 5, BucketType.user)
    async def donate(self, ctx:Context):
        '''
        Gives you the creator's donation links
        '''

        links = []
        if self.bot.config['paypal']:
            links.append(f"PayPal: <{self.bot.config['paypal']}>")
        if self.bot.config['patreon']:
            links.append(f"Patreon: <{self.bot.config['patreon']}>")
        if not links:
            return 
        await ctx.send('\n'.join(links))        


    @command()
    @cooldown(1, 5, BucketType.user)
    async def invite(self, ctx:Context):
        '''
        Gives you an invite link for the bot
        '''

        await ctx.send(
            f"<https://discordapp.com/oauth2/authorize?client_id={self.bot.user.id}&scope=bot&permissions=35840>"
        )


    @command(aliases=['guild', 'support'])
    @cooldown(1, 5, BucketType.user)
    async def server(self, ctx:Context):
        '''
        Gives you a server invite link
        '''

        await ctx.send(self.bot.config['guild'])


    @command(hidden=True)
    @cooldown(1, 5, BucketType.user)
    async def echo(self, ctx:Context, *, content:str):
        '''
        Echos a saying
        '''

        await ctx.send(content)


    @command(aliases=['status'])
    @cooldown(1, 5, BucketType.user)
    async def stats(self, ctx:Context):
        '''
        Gives you the stats for the bot
        '''       

        # await ctx.channel.trigger_typing()
        embed = Embed(
            colour=0x1e90ff
        )
        embed.set_footer(text=str(self.bot.user), icon_url=self.bot.user.avatar_url)
        embed.add_field(name="MarriageBot", value="A robot for marrying your friends and adopting your enemies.")
        creator = self.bot.get_user(self.bot.config["owners"][0])
        embed.add_field(name="Creator", value=f"{creator!s}\n{creator.id}")
        embed.add_field(name="Library", value=f"Discord.py {dpy_version}")
        embed.add_field(name="Guild Count", value=len(self.bot.guilds))
        embed.add_field(name="Shard Count", value=self.bot.shard_count)
        embed.add_field(name="Average Latency", value=f"{(self.bot.latency * 1000):.2f}ms")
        embed.add_field(name="Member Count", value=sum((len(i.members) for i in self.bot.guilds)))
        embed.add_field(name="Coroutines", value=f"{len([i for i in Task.all_tasks() if not i.done()])} running, {len(Task.all_tasks())} total.")
        embed.add_field(name="Process ID", value=self.process.pid)
        embed.add_field(name="CPU Usage", value=f"{self.process.cpu_percent():.2f}")
        embed.add_field(name="Memory Usage", value=f"{self.process.memory_info()[0]/2**20:.2f}MB/{virtual_memory()[0]/2**20:.2f}MB")
        ut = self.bot.get_uptime()  # Uptime
        uptime = [
            int(ut // (60*60*24)),
            int((ut % (60*60*24)) // (60*60)),
            int(((ut % (60*60*24)) % (60*60)) // 60),
            ((ut % (60*60*24)) % (60*60)) % 60,
        ]
        embed.add_field(name="Uptime", value=f"{uptime[0]} days, {uptime[1]} hours, {uptime[2]} minutes, and {uptime[3]:.2f} seconds.")
        embed.add_field(name="Family Members", value=len(FamilyTreeMember.all_users) - 1)
        try:
            await ctx.send(embed=embed)
        except Exception:
            await ctx.send("I tried to send an embed, but I couldn't.")


    @command(aliases=['clean'])
    async def clear(self, ctx:Context):
        '''
        Clears the bot's commands from chat
        '''

        if ctx.channel.permissions_for(ctx.guild.me).manage_messages:
            _ = await ctx.channel.purge(limit=100, check=lambda m: m.author.id == self.bot.user.id)
        else:
            _ = await ctx.channel.purge(limit=100, check=lambda m: m.author.id == self.bot.user.id, bulk=False)
        await ctx.send(f"Cleared `{len(_)}` messages from chat.")


def setup(bot:CustomBot):
    x = Misc(bot)
    bot.add_cog(x)
