# MarriageBot

[![Discord Bots](https://discordbots.org/api/widget/status/468281173072805889.svg)](https://discordbots.org/bot/468281173072805889)

This is a small Discord bot intended to bring love to your Discord servers. What it does is allows two users to get married. There are no benefits or drawbacks to being married. It simply is a thing that you can do. Here's a family tree you can make through marrying and adopting various users:

![A large family tree composed entirely of Discord users](https://marriagebot.xyz/static/images/tree.png)

## Me

I'm `Kae#0004`. Feel free to ask for help at any time. If you like what I do, then [feel free to help out](https://patreon.com/join/CalebB).

## Thanks

Thanks to all of you on the Landfall Games server for helping with the testing, especially Danny who I agreed I would give a specific shoutout too.

Thanks to Graphwiz for being a free piece of software that I can use at my leisure.

# Commands

Note: there's no command to accept or decline a proposal. Just say something along the lines of "yes" or "no" into chat, and it'll interpret that from there.

* `m!propose @User#1231`
This command allows you to initiate a marriage with another user. They, of course, can then deny your proposal, but that's unimportant

* `m!divorce @User#1231`
This does the opposite of the marry command, as you can imagine. It opens you back up to the dating pool.

* `m!adopt @User#1231`
Lets you try to adopt the mentioned user.

* `m!makeparent @User#1231`
Asks the person to be your parent. This will further restrict you from the dating pool, but makes your fake family trees look cooler.

* `m!disown @User#1231`
Allows you to disown one of your children.

* `m!emancipate @User#1231`
The equivelant of running away from home. Removes your parent.

* `m!partner [@User#1231]`
Shows who the user's partner is. Defaults to yourself.

* `m!parent [@User#1231]`
Shows who the user's parent is. Defaults to yourself.

* `m!relationship @User#1231 [@User2#4564]`
Shows you the relationship beteween the two given users (or the first user and yourself).

* `m!familysize [@User#1231]`
Gives you the amount of people in your family tree.

* `m!tree [@User#1231]`
Shows the family tree of the given user on the server the command was called from. Defaults to yourself. The bot needs to be able to send images to do this.

* `m!globaltree [@User#1231]`
Shows the family tree of the given user across all servers (since families persist over different servers). Defaults to yourself. The bot needs to be able to send images to do this.

* `m!treefile [@User#1231]`
Gives you the full family tree output for the given user as a .ged file.

* `m!prefix [Prefix]`
For when `m!` isn't good enough (you must have the `manage_guild` permission to run this command. You'll always be able to mention the bot to get its attention, so don't worry about forgetting the prefix).

# Testimonials

![Testimonial 1](https://marriagebot.xyz/static/images/testimonials/1.png)
![Testimonial 2](https://marriagebot.xyz/static/images/testimonials/2.png)
![Testimonial 3](https://marriagebot.xyz/static/images/testimonials/3.png)
![Testimonial 5](https://marriagebot.xyz/static/images/testimonials/5.png)
![Testimonial 6](https://marriagebot.xyz/static/images/testimonials/6.png)
![Testimonial 7](https://marriagebot.xyz/static/images/testimonials/7.png)
![Testimonial 8](https://marriagebot.xyz/static/images/testimonials/8.png)

# Self-Hosting

To host this bot yourself, you will need to install Python 3.6 or above, as well as the Discord.py rewrite (listed in `requirements.txt`). The database that *I* use is Postgres, and the SQL to generate the database and all relevant tables is included in the `config` folder, though you will have to edit and rename the `config/config.toml` file to work properly for your database setup.

After you set up *the database*,  *redis*, and *Graphviz*, install the requirements (which are listed in `requirements.txt`) and you're good to go.
