from discord.ext.commands import UserConverter, BadArgument


class UserID(int):
    async def convert(self, ctx, value) -> int:
        v = None
        try: v = int(value)
        except ValueError: v = await UserConverter().convert(ctx, value)
        if v: return v 
        raise BadArgument()
