from discord.ext import commands

from cogs import utils


class Misc(utils.Cog):

    @commands.command(aliases=['git', 'code'], cls=utils.Command, requires_set_config=['github'])
    async def github(self, ctx:utils.Context):
        """Sends the GitHub Repository link"""

        await ctx.send(f"<{self.bot.config.get('github')}>")

    @commands.command(aliases=['support', 'guild'], cls=utils.Command, requires_set_config=['guild_invite'])
    async def server(self, ctx:utils.Context):
        """Gives the invite to the support server"""

        await ctx.send(f"<{self.bot.config.get('guild_invite')}>")

    @commands.command(cls=utils.Command)
    async def invite(self, ctx:utils.Context):
        """Gives you the bot's invite link"""

        await ctx.send(f"<{self.bot.get_invite_link()}>")

    @commands.command(cls=utils.Command)
    async def echo(self, ctx:utils.Context, *, content:utils.converters.CleanContent):
        """Echos the given content into the channel"""

        await ctx.send(content)


def setup(bot:utils.CustomBot):
    x = Misc(bot)
    bot.add_cog(x)
