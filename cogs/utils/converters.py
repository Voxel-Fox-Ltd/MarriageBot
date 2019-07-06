from discord.ext.commands import UserConverter, BadArgument


class UserID(int):
    async def convert(self, ctx, value) -> int:
        v = None
        try: 
            return (await UserConverter().convert(ctx, value)).id
        except Exception as e: 
            try:
                return int(value)
            except Exception:
                raise e
        raise BadArgument()
