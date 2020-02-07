# Redis Values

## Pub/Sub

### TriggerStartup

Triggers the running of the bot.startup() method for a given shard id

```json
{"shard_id": "INT"}
```

### TreeMemberUpdate

Triggers a tree member update for recaching a value

JSON is the tree member itself

### ProposalCacheAdd/ProposalCacheRemove

```json
{
    "instigator": "get_id(instigator)",
    "target": "get_id(target)",
    "cog": "cog",
    "timeout_time": "timeout_time.isoformat()"
}
```

### BlockedUserAdd/BlockedUserRemove

Pings the bot to add/remove a user to the bot's internal cache

```json
{
    "user_id": "INT",
    "blocked_user_id": "INT"
}
```

### EvAll

Pings some content for the bot to eval

```json
{
    "content": "The content to eval",
    "channel_id": "INT",
    "message_id": "INT",
    "exempt": [],
}
```

### UpdateGuildPrefix

Updates the prefix for a guild. Payload has EITHER `gold_prefix` or `prefix`.

```json
{
    "guild_id": "INT",
    "prefix": "m!"
}
```

### UpdateFamilyMaxMembers

Update the maximum family members allowed in a given guild. Applies only to MBG.

```json
{
    "guild_id": "INT",
    "max_family_members": "INT"
}
```

### UpdateIncestAllowed

Updates the bool of whether or not incest is allowed in a given guild. Applies only to MBG.

```json
{
    "guild_id": "INT",
    "allow_incest": true,
}
```

### UpdateMaxChildren

Update the maximum amount of children allowed for a set of roles in a given guild. Applies only to MBG.

```json
{
    "guild_id": "INT",
    "max_children": {
        "INT": "INT"
    }
}
```

### SendUserMessage

Ping a DM to a given user.

```json
{
    "user_id": "INT", 
    "content": "What you want to DM the user"
}
```

### DBLVote

Adds a user to the bot's DBL vote cache

```json
{
    "user_id": "INT", 
    "datetime": "ISO-format-datetime"
}
```

## Set/Get

### UserName-{user_id}

The name and discrim for a given user ID
