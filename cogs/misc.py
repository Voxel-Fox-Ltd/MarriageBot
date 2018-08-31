from asyncio import Task
from discord import Embed, __version__ as dpy_version
from discord.ext.commands import command, Context, cooldown
from discord.ext.commands.cooldowns import BucketType
from cogs.utils.custom_bot import CustomBot 
from cogs.utils.family_tree.family_tree_member import FamilyTreeMember


class Misc(object):

    def __init__(self, bot:CustomBot):
        self.bot = bot 


    @command(aliases=['git', 'code'])
    @cooldown(1, 5, BucketType.user)
    async def github(self, ctx:Context):
        '''
        Gives you a link to the bot's code repository
        '''

        await ctx.send(f"<{self.bot.config['github']}>")


    @command()
    @cooldown(1, 5, BucketType.user)
    async def patreon(self, ctx:Context):
        '''
        Gives you the creator's Patreon link
        '''

        await ctx.send(f"<{self.bot.config['patreon']}>")


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


    @command()
    @cooldown(1, 5, BucketType.user)
    async def stats(self, ctx:Context):
        '''
        Gives you the stats for the bot
        '''

        embed = Embed(
            colour=0x1e90ff
        )
        embed.set_footer(text=str(self.bot.user), icon_url=self.bot.user.avatar_url)
        embed.add_field(name="MarriageBot", value="A robot for marrying your friends and adopting your enemies.")
        creator = self.bot.get_user(self.bot.config["owner"])
        embed.add_field(name="Creator", value=f"{creator!s}\n{creator.id}")
        embed.add_field(name="Library", value=f"Discord.py {dpy_version}")
        embed.add_field(name="Guild Count", value=len(self.bot.guilds))
        embed.add_field(name="Member Count", value=sum((len(i.members) for i in self.bot.guilds)))
        embed.add_field(name="Coroutines", value=f"{len([i for i in Task.all_tasks() if not i.done()])} running, {len(Task.all_tasks())} total.")
        embed.add_field(name="Uptime", value=f"{self.bot.loop.time():.2f} seconds.")
        embed.add_field(name="Family Members", value=len(FamilyTreeMember.all_users) - 1)
        try:
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send("I tried to send an embed, but I couldn't.")


def setup(bot:CustomBot):
    x = Misc(bot)
    bot.add_cog(x)
