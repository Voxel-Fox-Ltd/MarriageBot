import requests


class Marriagebot(object):
    
    base_url = "http://vps.callumb.co.uk:5696"

    '''
    gets a json object of all the colours from the marriagebot api
    '''
    @classmethod
    def get_colours(cls, user_id):
        params = {
            "user_id":user_id
        }
        response = requests.get(url = (cls.base_url+"/user"),params = params)
        return response.json()

    '''
    sends the user selected colours back to the marriagebot api
    '''
    @classmethod
    def set_colours(cls, user_id,
                    edge,
                    node,
                    font,
                    background,
                    highlighted_node,
                    highlighted_font):
        
        payload = {
            "user_id": user_id,
            "edge":edge,
            "node":node,
            "font":font,
            "background":background,
            "highlighted_node":highlighted_node,
            "highlighted_font":highlighted_font
        }

        requests.post(url = cls.base_url+"/user",json = payload)
        return
    
    '''
    sends the user selected prefix to the marriagebot api
    '''
    @classmethod
    def set_prefix(cls, prefix,user_id,guild_id):
        payload = {
            "user_id":user_id,
            "guild_id":guild_id,
            "prefix":prefix
        }

        requests.post(url = cls.base_url+"/guild",json = payload)
        return

    @classmethod
    def get_prefix(cls, guild_id):
        params = {
            "guild_id":guild_id
        }
        response = requests.get(url = cls.base_url+"/guild",params=params)
        json = response.json()
        print(response.text)
        return json["guild_prefix"]


