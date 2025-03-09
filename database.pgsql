CREATE TABLE IF NOT EXISTS guild_settings(
    guild_id BIGINT NOT NULL,
    guild_specific_families BOOLEAN DEFAULT FALSE,
    allow_incest BOOLEAN DEFAULT FALSE,
    gifs_enabled BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (guild_id)
);
-- A config for a guild to change their prefix or other bot settings.


CREATE TABLE IF NOT EXISTS marriages(
    user_id BIGINT NOT NULL,
    partner_id BIGINT NOT NULL,
    guild_id BIGINT NOT NULL DEFAULT 0,
    timestamp TIMESTAMP,
    PRIMARY KEY (user_id, partner_id, guild_id)
);
-- A table to hold a user and their partner. The primary key
-- stops users from getting married twice. This may need revisiting
-- in the near future.


CREATE TABLE IF NOT EXISTS parents(
    child_id BIGINT NOT NULL,
    parent_id BIGINT NOT NULL,
    guild_id BIGINT NOT NULL DEFAULT 0,
    timestamp TIMESTAMP,
    PRIMARY KEY (child_id, guild_id)
);
-- A table holding a child and their parent. Since a child can only have
-- one parent (a decision made long ago), the child has been made the
-- primary key of the table.


CREATE TABLE IF NOT EXISTS guild_specific_families(
    guild_id BIGINT NOT NULL,
    purchased_by BIGINT,
    PRIMARY KEY (guild_id)
);
-- A list of guild IDs of people who've paid for Gold.


CREATE TABLE IF NOT EXISTS customisation(
    user_id BIGINT NOT NULL,
    edge INTEGER DEFAULT NULL,
    node INTEGER DEFAULT NULL,
    font INTEGER DEFAULT NULL,
    highlighted_font INTEGER DEFAULT NULL,
    highlighted_node INTEGER DEFAULT NULL,
    background INTEGER DEFAULT NULL,
    direction CHAR(2) DEFAULT 'TB',
    PRIMARY KEY (user_id)
);
-- A table for user tree customisations. The nulls are all set in the
-- bot's code for defaults.


CREATE TABLE IF NOT EXISTS usernames(
    id BIGINT PRIMARY KEY,
    name TEXT
);
