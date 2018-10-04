import requests
from json import dumps
from marriagebot import Marriagebot
from discord import Permissions

class User:

    def __init__(self,json_object):
        self.username = json_object["username"]
        self.locale = json_object["locale"]
        self.mfa_enabled = json_object["mfa_enabled"]
        self.avatar = json_object["avatar"]
        self.discriminator = json_object["discriminator"]
        self.id = json_object["id"]
        self.json = json_object
        self.guild_list = []
        self.selected_guild = ""
        
        
    
    '''
    gets the url of the user avatar
    size is between 1 and 7
    '''
    def get_avatar_url(self,size = 5) -> str:
        clamped_size = self.clamp(size,1,7)
        img_size = (2**(clamped_size+3))
        link = "https://cdn.discordapp.com/avatars/{}/{}.png?size={}".format(self.id,self.avatar,img_size)
        return link
    
    def get_guild(self,guild_id):
        for guild in self.guild_list:
            if (guild.id == guild_id):
                return guild
            
    

    def clamp(self,value,min,max):
        '''
        keeps value within min and max
        '''
        if(value>max):
            return max
        if(value<min):
            return min
        else:
            return value

    def __str__(self):
        return dumps(self.json)

    def get_name(self):
        return self.username+"#"+self.discriminator
