This file is going to be a brief explanation of how to set up your config file. It should be pretty simple, provided you know what you're doing.

```json
{
    "token": "Insert your bot token here",
    "dbl_token": "Leave this blank, most likely",
    "owners": [
        Put_your_ID_here
    ], 
    "bot_admin_role": This_role_can_use_commands_from_bot_moderator,
    "patreon_roles": [
        This_role_will_return_true_for_is_donator
    ],
    "database": {
        "user": "Postgres Username" ,
        "password": "Postgres Password",
        "database": "Postgres Database",
        "host": "127.0.0.1"
    },
    "redis": {
        "host": "127.0.0.1",
        "port": 6379,
        "db": 0
    },
    "google_analytics": {
        "tracking_id": "Put your GA tracking ID here",
        "app_name": "Call this whatever you want",
        "document_host": "Call this whatever you want - it should *really* be a URL but whatever"
    },
    "oauth": {
        "client_id": "Your Oauth client ID",
        "client_secret": "Your Oauth client secret",
        "redirect_uri": "Your Oauth redirect URI"
    },
    "ssl_context": {
        "certfile": "Certfile path for your SSL context",
        "keyfile": "Keyfile path for your SSL context"
    },
    "footer": [
        {"text": "Footer text for your embed", "amount": 1}
    ],
    "presence_text": "What the bot will be playing",
    "default_prefix": "What prefix should the bot have",
    "tree_file_location": "Where should your trees be output to",
    "dbl_vainity": "Your DBL vainity link - leave this blank probably",
    "github": "https://github.com/4Kaylum/MarriageBot",
    "patreon": "https://patreon.com/join/CalebB",
    "paypal": "https://paypal.me/CalebBartlett",
    "guild": "Link to the bot's support server - leave this blank probably",
    "embed_default_text": null
}```