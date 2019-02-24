from os import getpid
from asyncio import Task
from random import choice, randint
from datetime import datetime as dt, timedelta

from psutil import Process, virtual_memory
from discord import Embed, __version__ as dpy_version
from discord.ext.commands import command, Context, Cog, cooldown
from discord.ext.commands import CommandOnCooldown
from discord.ext.commands.cooldowns import BucketType

from cogs.utils.custom_bot import CustomBot 
from cogs.utils.family_tree.family_tree_member import FamilyTreeMember


class Misc(Cog):

    def __init__(self, bot:CustomBot):
        self.bot = bot 
        pid = getpid()
        self.process = Process(pid)
        self.process.cpu_percent()


    async def cog_command_error(self, ctx:Context, error):
        '''
        Local error handler for the cog
        '''

        # Cooldown
        if isinstance(error, CommandOnCooldown):
            if ctx.author.id in self.bot.config['owners']:
                await ctx.reinvoke()
            else:
                await ctx.send(f"You can only use this command once every `{error.cooldown.per:.0f} seconds` per server. You may use this again in `{error.retry_after:.2f} seconds`.")
            return


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


    @command(name='help', hidden=True)
    async def newhelp(self, ctx:Context, *, command_name:str=None):
        '''
        Gives you the new help command uwu
        '''

        # Get all the cogs
        cogs = self.bot.cogs.values()

        # Get all the commands from the cogs
        cog_commands = [cog.get_commands() for cog in cogs]

        # See which the user can run
        runnable_commands = []
        for cog in cog_commands:
            runnable_cog = []
            for command in cog:
                try:
                    runnable = await command.can_run(ctx) and command.hidden == False
                except Exception:
                    runnable = False 
                if runnable:
                    runnable_cog.append(command) 
            runnable_cog.sort(key=lambda x: x.name.lower())
            if len(runnable_cog) > 0:
                runnable_commands.append(runnable_cog)

        # Sort cogs list based on name
        runnable_commands.sort(key=lambda x: x[0].cog_name.lower())

        # Make an embed
        help_embed = Embed()
        help_embed.set_author(name=self.bot.user, icon_url=self.bot.user.avatar_url)
        help_embed.colour = randint(1, 0xffffff)
        dbl_link = self.bot.config['dbl_vainity'] or self.bot.user.id
        extra = [
            {'text': 'MarriageBot - Made by Caleb#2831'},
            {'text': f'MarriageBot - Add me to your own server! ({ctx.prefix}invite)'}
        ]
        if self.bot.config.get('dbl_token'):
            extra.append({'text': f'MarriageBot - Add a vote on Discord Bot List! ({ctx.prefix}vote)'})
        if self.bot.config.get('patreon'):
            extra.append({'text': f'MarriageBot - Support me on Patreon! ({ctx.prefix}patreon)'})
        if self.bot.config.get('guild'):
            extra.append({'text': f'MarriageBot - Join the official Discord server! ({ctx.prefix}server)'})
        help_embed.set_footer(**choice(extra))

        # Add commands to it
        for cog_commands in runnable_commands:
            value = '\n'.join([f"{ctx.prefix}{command.qualified_name} - *{command.short_doc}*" for command in cog_commands])
            help_embed.add_field(
                name=cog_commands[0].cog_name,
                value=value
            )
        
        # Send it to the user
        try:
            await ctx.author.send(embed=help_embed)
            await ctx.send('Sent you a PM!')
        except Exception:
            await ctx.send("I couldn't send you a PM :c")


def setup(bot:CustomBot):
    x = Misc(bot)
    bot.add_cog(x)
