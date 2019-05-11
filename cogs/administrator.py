from discord.ext.commands import command, Context, BucketType, cooldown
from discord.ext.commands import MissingPermissions, CommandOnCooldown

from cogs.utils.custom_bot import CustomBot
from cogs.utils.custom_cog import Cog


class Administrator(Cog): 

    def __init__(self,bot:CustomBot):
        super().__init__(self.__class__.__name__)
        self.bot = bot 


    async def cog_command_error(self, ctx:Context, error):
        '''
        Local error handler for the cog
        '''

        # Throw errors properly for me
        if ctx.author.id in self.bot.config['owners'] and not isinstance(error, CommandOnCooldown):
            text = f'```py\n{error}```'
            await ctx.send(text)
            raise error

        # Missing permissions
        if isinstance(error, MissingPermissions):
            await ctx.send(f"You need the `{error.missing_perms[0]}` permission to run this command.")
            return

        # Cooldown
        elif isinstance(error, CommandOnCooldown):
            if ctx.author.id in self.bot.config['owners']:
                await ctx.reinvoke()
            else:
                await ctx.send(f"You can only use this command once every `{error.cooldown.per:.0f} seconds` per server. You may use this again in `{error.retry_after:.2f} seconds`.")
            return


    async def cog_check(self, ctx:Context):
        if ctx.author.id in self.bot.config['owners']:
            return True
        if ctx.author.permissions_in(ctx.channel).manage_guild:
            return True
        raise MissingPermissions(["manage_guild"])


    @command()
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
                await db('INSERT INTO guild_settings VALUES ($1, $2)', ctx.guild.id, prefix)
            except Exception as e:
                await db('UPDATE guild_settings SET prefix=$1 WHERE guild_id=$2', prefix, ctx.guild.id)
        self.bot.guild_prefixes[ctx.guild.id] = prefix
        await ctx.send(f"Your guild's prefix has been udpated to `{prefix}`.")


def setup(bot:CustomBot):
    x = Administrator(bot)
    bot.add_cog(x)
