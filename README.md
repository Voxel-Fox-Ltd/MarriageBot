# MarriageBot

[![Discord Bots](https://discordbots.org/api/widget/status/468281173072805889.svg)](https://discordbots.org/bot/468281173072805889)

This is a small Discord bot intended to bring love to your Discord servers. What it does is allows two users to get married. There are no benefits or drawbacks to being married. It simply is a thing that you can do. Here's a family tree you can make through marrying and adopting various users:

![A large family tree composed entirely of Discord users](https://sparcli.callumb.co.uk/marriagebot/tree.png)

## Me

I'm `Caleb#2831`. Feel free to ask for help at any time. If you like what I do, then [feel free to help out](https://patreon.com/CallumBartlett).

## Thanks

Thanks to all of you on the Landfall Games server for helping with the testing, especially Danny who I agreed I would give a specific shoutout too.

Thank you to [Adrien Vergé for familytreemaker.py](https://github.com/adrienverge/familytreemaker), which I am shamelessly using in my own project.

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

* `m!tree [@User#1231]`
Shows the family tree of the given user on the server the command was called from. Defaults to yourself. The bot needs to be able to send images to do this.

* `m!globaltree [@User#1231]`
Shows the family tree of the given user across all servers (since families persist over different servers). Defaults to yourself. The bot needs to be able to send images to do this.

* `m!treefile [@User#1231]`
Gives you the full family tree output for the given user as a .ged file.

# Testimonials

![Testimonial 1](https://files.callumb.co.uk/marriagebot/1.png)
![Testimonial 2](https://files.callumb.co.uk/marriagebot/2.png)
![Testimonial 3](https://files.callumb.co.uk/marriagebot/3.png)
![Testimonial 5](https://files.callumb.co.uk/marriagebot/5.png)
![Testimonial 6](https://files.callumb.co.uk/marriagebot/6.png)
![Testimonial 7](https://files.callumb.co.uk/marriagebot/7.png)
![Testimonial 8](https://files.callumb.co.uk/marriagebot/8.png)
![Testimonial 9](https://files.callumb.co.uk/marriagebot/9.png)

# Self-Hosting

To host this bot yourself, you will need to install Python 3.6 or above, as well as the Discord.py rewrite. The database that *I* use is Postgres, and the SQL to generate the database and all relevant tables is included in the `config` folder, though you will have to edit and rename the `config/config.json` file to work properly for your database setup.

After you set up the database, install the requirements (which are just Discord.py rewrite and Graphwiz) and you're good to go.
