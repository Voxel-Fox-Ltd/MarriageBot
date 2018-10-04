import requests
class Marriagebot(object):
    base_url = "http://vps.callumb.co.uk:5696"

    '''
    gets a json object of all the colours from the marriagebot api
    '''
    @staticmethod
    def get_colours(user_id):
        params = {
            "user_id":user_id
        }
        response = requests.get(url = (Marriagebot.base_url+"/user"),params = params)
        return response.json()

    '''
    sends the user selected colours back to the marriagebot api
    '''
    @staticmethod
    def set_colours(user_id,
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

        requests.post(url = Marriagebot.base_url+"/user",json = payload)
        return
    
    '''
    sends the user selected prefix to the marriagebot api
    '''
    @staticmethod
    def set_prefix(prefix,user_id,guild_id):
        payload = {
            "user_id":user_id,
            "guild_id":guild_id,
            "prefix":prefix
        }

        requests.post(url = Marriagebot.base_url+"/guild",json = payload)
        return

    @staticmethod
    def get_prefix(guild_id):
        params = {
            "guild_id":guild_id
        }
        response = requests.get(url = Marriagebot.base_url+"/guild",params=params)
        json = response.json()
        print(response.text)
        return json["guild_prefix"]


