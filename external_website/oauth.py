import requests
from urllib.parse import urlencode
from user import User
from discord import Permissions
from guild import Guild


class Oauth(object):

    def __init__(self, *, client_id:str=None, client_secret:str=None):
        self.redirect_uri = "http://mb.callumb.co.uk:5000/login"
        self.scopes = "identify guilds"
        self.client_id = client_id
        self.client_secret = client_secret
        self.authorization_url = "https://discordapp.com/oauth2/authorize?" + urlencode({
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": self.scopes
        })
        self.discord_api_endpoint = "https://discordapp.com/api/oauth2/token"


    '''
    gets a user object of the user credentials
    from a json object from discord
    '''
    def get_user_credentials(self,access_token:str):
        base_url = "http://discordapp.com/api/users/@me"
        headers = {
            "Authorization" : f"Bearer {access_token}"
        }
        response_object = requests.post(url = base_url, headers=headers)
        user_json = response_object.json()
        user_object = User(user_json)
        user_object.guild_list = self.get_guild_list(headers,base_url)
    
        return user_object
    
    def get_guild_list(self,headers,base_url):
        guild_response = requests.get(url = (base_url+"/guilds"),headers = headers)
        guild_json = guild_response.json()
        owned_guild_list = []
        
        '''
        iterate through all the guilds
        if admin, manage guild or owner, add to list
        '''
        for guild in guild_json:
            permission = Permissions(guild['permissions'])#create permission object
            if((guild["owner"] == True)or(permission.manage_guild)or(permission.administrator)):
                guild_object = Guild(guild)
                owned_guild_list.append(guild_object)
        return owned_guild_list
                


    '''
    gets the token that can be exchanged for the 
    user object from the discord api
    '''
    def get_token(self,code:str):
        self.code = code
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "code": self.code,
            "redirect_uri": self.redirect_uri,
            "scope": self.scopes
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded" 
        }
        response = requests.post(self.discord_api_endpoint, data=payload, headers=headers)
        json_object = response.json()
        return json_object["access_token"]

