CREATE TABLE marriages(
    user_id BIGINT NOT NULL,
    partner_id BIGINT NOT NULL,
    guild_id BIGINT NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, guild_id)
);
-- This table will hold marraiges both in date and divorced pairs
-- marriage_id will be a random 11-character string
-- user_id will be one of the users involved (the other user will get an entry with an identical marriage_id)


CREATE TABLE parents(
    child_id BIGINT NOT NULL,
    parent_id BIGINT NOT NULL,
    guild_id BIGINT NOT NULL DEFAULT 0,
    PRIMARY KEY (child_id, guild_id)
);
-- Since a child will only appear once, you can set child_id to the primary key
-- A parent can have many children, a child will have only one parent


CREATE TABLE blacklisted_guilds(
    guild_id BIGINT NOT NULL,
    PRIMARY KEY (guild_id)
);
-- Basically a big ol' list of blacklisted guild IDs


CREATE TABLE guild_specific_families(
    guild_id BIGINT NOT NULL,
    PRIMARY KEY (guild_id)
);
-- A big ol' list of guild IDs of people who've paid


CREATE TABLE guild_settings(
    guild_id BIGINT NOT NULL,
    prefix VARCHAR(30) DEFAULT 'm!',
    allow_incest BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (guild_id)
);
-- A config for a guild to change their prefix or other bot settings


CREATE TYPE direction AS ENUM('TB', 'LR');
CREATE TABLE customisation(
    user_id BIGINT NOT NULL,
    edge INTEGER DEFAULT NULL,
    node INTEGER DEFAULT NULL,
    font INTEGER DEFAULT NULL,
    highlighted_font INTEGER DEFAULT NULL,
    highlighted_node INTEGER DEFAULT NULL,
    background INTEGER DEFAULT NULL,
    direction direction DEFAULT 'TB',
    PRIMARY KEY (user_id)
);
-- A table for user tree customisations


CREATE TABLE command_log(
    guild_id BIGINT,
    channel_id BIGINT,
    user_id BIGINT,
    message_id BIGINT PRIMARY KEY,
    content VARCHAR(2000),
    command_name VARCHAR(100),
    invoked_with VARCHAR(100),
    command_prefix VARCHAR(2000),
    timestamp TIMESTAMP,
    command_failed BOOLEAN,
    valid BOOLEAN,
    shard_id SMALLINT
);


CREATE TABLE blocked_user(
    user_id BIGINT,
    blocked_user_id BIGINT,
    PRIMARY KEY (user_id, blocked_user_id)
);
-- A user and how they're blocked ie user_id is the person who blocks blocked_user_id


CREATE TABLE dbl_votes(
    user_id BIGINT PRIMARY KEY,
    timestamp TIMESTAMP
);
-- A table to track the last time a user voted for the bot


CREATE TABLE shard_logging(
        message_create INTEGER,
        message_edit INTEGER,
        typing_start INTEGER,
        message_delete INTEGER,
        reaction_add INTEGER,
        reaction_remove INTEGER,
        reaction_clear INTEGER,
        channel_create INTEGER,
        channel_delete INTEGER,
        channel_update INTEGER,
        member_join INTEGER,
        member_remove INTEGER,
        member_update INTEGER,
        guild_join INTEGER,
        guild_remove INTEGER,
        guild_update INTEGER,
        role_create INTEGER,
        role_delete INTEGER,
        role_update INTEGER,
        emoji_update INTEGER,
        voice_state_update INTEGER,
        member_ban INTEGER,
        member_unban INTEGER,
        latency DECIMAL,
        shard_id INTEGER,
        timestamp TIMESTAMP,
        PRIMARY KEY (shard_id, timestamp)
);
-- Simple event counter as logging for shards


CREATE TABLE blog_posts(
    url VARCHAR(50) PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    body TEXT NOT NULL,
    created_at TIMESTAMP
);
