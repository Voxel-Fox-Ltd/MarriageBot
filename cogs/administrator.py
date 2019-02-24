from discord.ext.commands import command, Context, MissingPermissions, BucketType, Cog

from cogs.utils.custom_bot import CustomBot
from cogs.utils.checks.cooldown import cooldown


class Administrator(Cog): 

    def __init__(self,bot:CustomBot):
        self.bot = bot 


    async def cog_check(self, ctx:Context):
        if ctx.author.permissions_in(ctx.channel).manage_guild:
            return True
        raise MissingPermissions(["manage_guild"])


    @command(hidden=True)
    @cooldown(1, 5, BucketType.guild)
    async def prefix(self, ctx:Context, prefix:str=None):
        '''
        Changes the prefix for your guild
        '''

        if not prefix:
            prefix = self.bot.config['default_prefix']
        if len(prefix) > 30:
            await ctx.send("Your prefix can't be longer than 30 characters, I'm afraid.")
            return

        async with self.bot.database() as db:
            try:
                await db('INSERT INTO guid_settings VALUES ($1, $2)', ctx.guild.id, prefix)
            except Exception as e:
                await db('UPDATE guild_settings SET prefix=$1 WHERE guild_id=$2', prefix, ctx.guild.id)
        self.bot.guild_prefixes[ctx.guild.id] = prefix
        await ctx.send(f"Your guild's prefix has been udpated to `{prefix}`.")


def setup(bot:CustomBot):
    x = Administrator(bot)
    bot.add_cog(x)
