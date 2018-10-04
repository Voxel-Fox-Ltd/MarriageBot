from marriagebot import Marriagebot
class Guild:

    def __init__(self,json):
        self.id = json["id"]
        self.name = json["name"]
        self.icon = json["icon"]
        self.json = json
        self.icon_url = self.get_icon_url()
        self.prefix = self.get_prefix()


    
    def get_icon_url(self):
        base_url = "https://cdn.discordapp.com/"
        url = "{}icons/{}/{}.png".format(base_url,self.id,self.icon)
        return url

    def get_prefix(self):
        return Marriagebot.get_prefix(self.id)
