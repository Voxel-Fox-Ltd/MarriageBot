CREATE TABLE command_log(
    guild_id BIGINT,
    channel_id BIGINT,
    user_id BIGINT, 
    message_id BIGINT PRIMARY KEY,
    content VARCHAR(2000),
    command_name VARCHAR(100),
    invoked_with VARCHAR(100),
    command_prefix VARCHAR(2000),
    timestamp TIMESTAMP
);
