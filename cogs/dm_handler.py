import discord
from discord.ext import commands

from cogs import utils


class DMHandler(utils.Cog):

    def __init__(self, bot:utils.Bot):
        super().__init__(bot)
        self.forward_dms = False
        self.owner = None

    @utils.Cog.listener()
    async def on_message(self, message:discord.Message):
        """Forwards DMs to the OwOner"""

        if not self.forward_dms:
            return
        if message.guild:
            return
        if message.author.bot:
            return
        if message.content.lower().startswith(self.bot.config['prefix']['default_prefix']):
            return
        if message.author.id in self.bot.config['owners']:
            return
        owner = self.owner or await self.bot.fetch_user(self.bot.config['owners'][0])
        content = f'__**FROM {message.author.id}**__'
        if message.content:
            content += '\n' + message.content
        if message.attachments:
            content += '\nAttachments: ' + ', '.join([i.url for i in message.attachments])
        await owner.send(content)

    @commands.command(cls=utils.Command)
    @commands.is_owner()
    async def toggledms(self, ctx):
        self.forward_dms = not self.forward_dms
        if self.forward_dms:
            return await ctx.send("DM forwarding enabled.")
        return await ctx.send("DM forwarding disabled.")


def setup(bot:utils.Bot):
    x = DMHandler(bot)
    bot.add_cog(x)
