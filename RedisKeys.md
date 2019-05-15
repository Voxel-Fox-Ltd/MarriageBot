# Redis Values

## Pub/Sub

### TriggerStartup

Triggers the running of the bot.startup() method for a given shard id

```json
{'shard_id': N}
```

### TreeMemberUpdate

Triggers a tree member update for recaching a value

JSON is the tree member itself

### ProposalCacheAdd/ProposalCacheRemove

```json
'instigator': get_id(instigator),
'target': get_id(target),
'cog': cog,
'timeout_time': timeout_time.isoformat()
```

## Set/Get

### UserName-{user_id}

The name and discrim for a given user ID
