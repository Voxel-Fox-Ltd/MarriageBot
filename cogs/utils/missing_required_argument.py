from discord.ext import commands


class MissingRequiredArgumentString(commands.MissingRequiredArgument):

    def __init__(self, param:str):
        self.param = param
