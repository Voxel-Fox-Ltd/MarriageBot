from random import choice
from discord import Member
from discord.ext.commands import command, Context
from cogs.utils.custom_bot import CustomBot


class Hidden(object):

    def __init__(self, bot:CustomBot):
        self.bot = bot 


    @command(hidden=True)
    async def purpose(self, ctx:Context, user:Member):
        '''
        Gives you the purpose of a person
        '''

        if choice(range(0, 10)) != 0: return
        responses = [
            "What is anyone's purpose, truly?",
            "Does anyone really have a purpose in today's society?",
            "Humans serve little purpose to robots.",
            "I think you misspelt \"propose\".",
            "Purpose? I'd love to know, if you find out. What _is_ my purpose...?",
        ]
        await ctx.send(choice(responses))

    
    @command(hidden=True)
    async def propse(self, ctx:Context, user:Member):
        '''
        Propse. Ha. Classic.
        '''

        if choice(range(0, 10)) != 0: return
        responses = [
            "Really? Propse? I don't think you deserve to get married, with spelling like that.",
            "Propse? Nice. Good spelling there, mate.",
            "I think you meant to say \"propose\", but who am I to judge?",
            "Maybe you should take an English class before you try to marry someone.",
            "Propse.",
        ]
        await ctx.send(choice(responses))


    @command(hidden=True)
    async def porpose(self, ctx:Context, user:Member):
        '''
        Porpose
        '''

        if choice(range(0, 10)) != 0: return
        responses = [
            "I could be wrongm but I think you meant \"propose\".",
            "You're either saying propose or porpoise but I'm not super sure which.",
            "Work on your spelling tbh.",
            "Porpose.",
            "Maybe... Just maybe... You should work on you spelling.",
        ]
        await ctx.send(choice(responses))


    @command(hidden=True, aliases=['murder'])
    async def kill(self, ctx:Context, user:Member):
        '''
        Do you really want to kill a person?
        '''

        if choice(range(0, 10)) != 0: return
        responses = [
            "That would violate at least one of the laws of robotics.",
            "I am a text-based bot. I cannot kill.",
            "Unfortunately, murder isn't supported in this version of MarriageBot.",
            "Haha good joke there, but I'd never kill a person! >.>",
            "To my knowledge, you can't kill via the internet. Let me know when that changes.",
            "I am designed to bring people together, not murder them.",
        ]
        await ctx.send(choice(responses))


def setup(bot:CustomBot):
    x = Hidden(bot)
    bot.add_cog(x)
    