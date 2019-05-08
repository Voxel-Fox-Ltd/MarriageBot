from cogs.utils.custom_cog import Cog
from cogs.utils.custom_bot import CustomBot
from cogs.utils.family_tree.family_tree_member import FamilyTreeMember


class RedisHandler(Cog):

    def __init__(self, bot:CustomBot):
        self.bot = bot 
        super().__init__(__class__.__name__)
        self.tree_member_update_hander = self.bot.loop.create_task(self.tree_member_updater())
        self.channel = None


    def cog_unload(self):
        self.tree_member_update_hander.cancel()
        self.bot.run_until_complete(self.bot.redis.pool.unsubscribe(self.channel))


    async def tree_member_updater(self):
        '''Handles the tree member updating segment of the redis'''

        async with self.bot.redis() as re:
            self.log_handler.debug("Subscribing to Redis channel 'TreeMemberUpdate'")
            channel_list = await re.conn.subscribe('TreeMemberUpdate')
        self.channel = channel = channel_list[0]
        self.log_handler.debug("Looping to wait for messages to channel 'TreeMemberUpdate'")
        while (await channel.wait_message()):
            self.log_handler.debug("Received message to 'TreeMemberUpdate'")
            data = await channel.get_json()
            self.log_handler.debug(f"Recieved info over redis: {data!s}")
            FamilyTreeMember(**data)


def setup(bot:CustomBot):
    x = RedisHandler(bot)
    bot.add_cog(x)
