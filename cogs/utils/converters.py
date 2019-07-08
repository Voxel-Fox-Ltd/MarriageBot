from discord.ext.commands import UserConverter, BadArgument, Converter


class UserID(Converter):
    async def convert(self, ctx, value) -> int:

        # Try userconverter
        try: 
            v = await UserConverter().convert(ctx, value) 
            if v:
                return v.id
        except Exception:
            pass

        # Try int (see if it's an ID already)
        try:
            return int(value)
        except ValueError:
            pass 
        
        # See if it's a mention
        try:
            return int(value.strip('<>!@'))
        except ValueError:
            pass 

        # Ah well
        raise BadArgument()
