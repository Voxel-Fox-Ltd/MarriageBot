from requests import get
import json

from discord.ext import commands
from cogs import utils
from discord import Embed, Colour


class Contributor:
    def __init__(self, dic):
        self.username = dic["author"]["login"]
        self.avatar = dic["author"]["avatar_url"]
        self.profile = dic["author"]["html_url"]
        self.commits = dic["total"]

class Contributors(utils.Cog):
    
    @commands.command(aliases=["contributors"], cls=utils.Command)
   # @utils.checks.bot_is_ready()
    @commands.bot_has_permissions(send_messages=True)
    async def get_contributors(self, ctx:utils.Context):
        API_URL = "https://api.github.com/repos/Voxel-Fox-Ltd/MarriageBot/stats/contributors"
        contributors = []
        res = get(API_URL).json()
        for i in res:
           contributors.append(Contributor(i))
        contributors.sort(key = lambda x:x.commits, reverse = True)
        embed = Embed(title="Contributors of Marriage Bot", colour=Colour.blue())
        text=""
        for i,cont in enumerate(contributors, start=1):
            text+=f"{i}. **[{cont.username}]({cont.profile})** 🔨{cont.commits} commits.\n"
        embed.add_field(name="GitHub contributors", value=text)
        await ctx.send(embed=embed)
    
def setup(bot:utils.Bot):
    x = Contributors(bot)
    bot.add_cog(x)
