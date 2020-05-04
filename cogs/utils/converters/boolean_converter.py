from discord.ext import commands


class BooleanConverter(commands.Converter):

    @classmethod
    async def convert(self, ctx, argument):

        return any([
            argument.lower() in ['y', 'yes', 'true', 'definitely', 'ye', 'ya', 'yas', 'ok', 'okay'],
            argument in ['\N{HEAVY CHECK MARK}', '<:tickYes:596096897995899097>'],
        ])
