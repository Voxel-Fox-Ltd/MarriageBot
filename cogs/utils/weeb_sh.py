import json


BASE_URL = "https://api.weeb.sh"
ALLOWED_REACTIONS = {
    "cry",
    "cuddle",
    "hug",
    "kiss",
    "pat",
    "slap",
    "tickle",
    "bite",
    "punch",
}


async def get_reaction_gif(bot, reaction_type:str):
    """Pings the endpoint, gets a reaction gif, bish bash bosh"""

    if not bot.config['api_keys']['weebsh']:
        bot.logger.debug("No API key set for Weeb.sh")
        return None
    if reaction_type not in ALLOWED_REACTIONS:
        bot.logger.debug(f"Invalid reaction {reaction_type} passed to get_reaction_gif")
        return None
    headers = {
        "User-Agent": "MarriageBot/1.0.0 ~ Discord@Kae#0004",
        "Authorization": f"Wolke {bot.config['api_keys']['weebsh']}"
    }
    params = {
        "type": reaction_type,
        "nsfw": "false",
    }
    async with bot.session.get(f"{BASE_URL}/images/random", params=params, headers=headers) as r:
        try:
            data = await r.json()
        except Exception as e:
            data = await r.text()
            bot.logger.warning(f"Error from Weeb.sh ({e}): {data}")
            return None
        if str(r.status)[0] == "2":
            return data['url']
    bot.logger.warning("Error from Weeb.sh: " + json.dumps(data))
