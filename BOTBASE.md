# DiscordpyBotBase

This is a base bot template that I tend to use in all of the bots I make. This skips all of the copy/pasting I would have to do for commands like invite, Github, all of the error handling and database handling, etc.

## How to use

This repository is marked as a template, so you should just be able to make a new repo based on this one. If you don't want to do that, you can add this repo as a remote and pull or clone it so you can make your own. It's all pretty alright, but I'm willing to take PRs or suggestions on how to make this better.

## What's in it

You may be thinking "why the heckie hoo would I use this?"

You'd be right! It's the same as normal D.py (mostly) with just a lil few changes. Which I'll now note!

### Database

I've included a database util! It's great! I like it! It uses PostgreSQL, using the data supplied in your [config file](config/config.example.json). Used like so:

```py
async with self.bot.database() as db:
    await db("INSERT INTO table_name (a, b, c) VALUES ($1, $2, $3)", 1, 2, 3)
    data = await db("SELECT * FROM table_name")
for row in data:
    print(row['a'])
```

### Redis

REDIS! What a gem. I've only used it a couple of times so I'm not a big expert and I've not added a whole bunch to the util for it, but it's used in much the same way as the database in terms of SET/GET at least.

```py
async with self.bot.redis() as re:
    await re.set("KEY", "Value")
    data = await re.get("KEY")
if data is not None:
    print(data)
```

### Cooldowns

Rapptz's cooldown handling is not great if you want to do anything more complicated than "you all get cooldowns for X time". You want cooldowns in some channels and not others? You want cooldowns based on roles? That's possible with this.

```py
@commands.command(cls=utils.Command)
@utils.cooldown.cooldown(1, 60, commands.BucketType.user, cls=utils.cooldown.RoleBasedCooldown())
async def commandname(self, ctx):
    ...

@commands.command(cls=utils.Command)
@utils.cooldown.cooldown(1, 60, commands.BucketType.user, cls=utils.cooldown.CooldownWithChannelExemptions(cooldown_in=["general"]))
async def commandname(self, ctx):
    ...
```

The current cooldowns I've got built into this right now aren't really wonderful but all of the systems are there for if you want to expand it.

### Context Embeds

Setting up embeds always looked a bit messy to me, so I just added support for the `with` syntax so I could clean it up a lil. Apart from that they work pretty much identically to normal embeds.

```py
with utils.Embed() as embed:
    embed.set_author(name="Test")
    embed.set_author_to_user(user=self.bot.get_user(user_id))
    embed.description = "Lorem ipsum"
    embed.use_random_colour()
```
