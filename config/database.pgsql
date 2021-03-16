CREATE TABLE marriages(
    user_id BIGINT NOT NULL,
    partner_id BIGINT NOT NULL,
    guild_id BIGINT NOT NULL DEFAULT 0,
    timestamp TIMESTAMP,
    PRIMARY KEY (user_id, guild_id)
);
-- This table will hold marraiges both in date and divorced pairs
-- marriage_id will be a random 11-character string
-- user_id will be one of the users involved (the other user will get an entry with an identical marriage_id)


CREATE TABLE parents(
    child_id BIGINT NOT NULL,
    parent_id BIGINT NOT NULL,
    guild_id BIGINT NOT NULL DEFAULT 0,
    timestamp TIMESTAMP,
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
    purchased_by BIGINT,
    PRIMARY KEY (guild_id)
);
-- A big ol' list of guild IDs of people who've paid


CREATE TABLE guild_settings(
    guild_id BIGINT NOT NULL,
    prefix VARCHAR(30) DEFAULT 'm!',
    gold_prefix VARCHAR(30) DEFAULT 'm.',
    allow_incest BOOLEAN DEFAULT FALSE,
    max_family_members INTEGER DEFAULT 500,
    gifs_enabled BOOLEAN DEFAULT TRUE,
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


CREATE TABLE blog_posts(
    url VARCHAR(50) PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    body TEXT NOT NULL,
    created_at TIMESTAMP,
    author_id BIGINT
);


CREATE TABLE paypal_purchases(
    id VARCHAR(64) NOT NULL PRIMARY KEY,
    customer_id VARCHAR(18),
    payment_amount INTEGER NOT NULL,
    discord_id BIGINT NOT NULL,
    guild_id BIGINT NOT NULL,
    completed BOOLEAN NOT NULL DEFAULT FALSE,
    checkout_complete_timestamp TIMESTAMP
);


CREATE TABLE channel_list(
    guild_id BIGINT,
    channel_id BIGINT,
    key VARCHAR(50),
    value VARCHAR(50),
    PRIMARY KEY (guild_id, channel_id, key)
);


CREATE TABLE redirects(
    code VARCHAR(50) PRIMARY KEY,
    location VARCHAR(2000)
);


CREATE TABLE random_text(
    command_name VARCHAR(50),
    event_name VARCHAR(50),
    string VARCHAR(2000),
    language_code VARCHAR(2),
    PRIMARY KEY (command_name, event_name, string, language_code)
);


CREATE TABLE disabled_commands(
    command_name VARCHAR(50) NOT NULL,
    guild_id BIGINT NOT NULL,
    disabled BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (command_name, guild_id)
);


CREATE TABLE max_children_amount(
    guild_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    amount INTEGER DEFAULT 5,
    PRIMARY KEY (guild_id, role_id)
);


CREATE TABLE user_settings(
    user_id BIGINT PRIMARY KEY
);


CREATE TABLE role_list(
    guild_id BIGINT,
    role_id BIGINT,
    key VARCHAR(50),
    value VARCHAR(50),
    PRIMARY KEY (guild_id, role_id, key)
);

CREATE TABLE IF NOT EXISTS ship_percentages(
    user_id_1 BIGINT,
    user_id_2 BIGINT,
    percentage SMALLINT,
    PRIMARY KEY (user_id_1, user_id_2)
);