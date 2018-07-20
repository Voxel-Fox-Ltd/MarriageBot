
# MarriageBot

This is a small Discord bot intended to bring love to your Discord servers. What it does is allows two users to get married. There are no benefits or drawbacks to being married. It simply is a thing that you can do.

## Me

I'm `Caleb#2831`. Feel free to ask for help at any time. If you like what I do, then [feel free to help out](https://patreon.com/CallumBartlett).

# Commands

* `m!propose @User#1231`
This command allows you to initiate a marriage with another user. They, of course, can then deny your proposal, but that's unimportant

* `m!divorce @User#1231`
This does the opposite of the marry command, as you can imagine. It opens you back up to the dating pool.

* `m!makeparent @User#1231`
Asks the person to be your parent. This will further restrict you from the dating pool, but makes your fake family trees look cooler.

* `m!disown @User#1231`
Allows you to disown one of your children.

* `m!partner [@User#1231]`
Shows who the user's partner is. Defaults to yourself.

* `m!parent [@User#1231]`
Shows who the user's parent is. Defaults to yourself.

* `m!tree [@User#1231]`
Shows the family tree of the given user. Defaults to yourself. The bot needs to be able to send images to do this.

# Self-Hosting

To host this bot yourself, you will need to install Python 3.6 or above, as well as the Discord.py rewrite. The database that *I* use is Postgres, and the SQL to generate the database and all relevant tables is included in the `config` folder, though you will have to edit and rename the `config/config.json` file to work properly for your database setup.
