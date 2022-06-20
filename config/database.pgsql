CREATE TABLE IF NOT EXISTS guild_settings(
    guild_id BIGINT NOT NULL,
    prefix VARCHAR(30) DEFAULT 'm!',
    gold_prefix VARCHAR(30) DEFAULT 'm.',
    test_prefix VARCHAR(30) DEFAULT 'm,',
    allow_incest BOOLEAN DEFAULT FALSE,
    max_family_members INTEGER DEFAULT 2000,
    gifs_enabled BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (guild_id)
);
-- A config for a guild to change their prefix or other bot settings.


CREATE TABLE IF NOT EXISTS user_settings(
    user_id BIGINT PRIMARY KEY
);
-- A user config table; not used but required for VBU.


CREATE TABLE IF NOT EXISTS marriages(
    user_id BIGINT NOT NULL,
    partner_id BIGINT NOT NULL,
    guild_id BIGINT NOT NULL DEFAULT 0,
    timestamp TIMESTAMP,
    PRIMARY KEY (user_id, guild_id)
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


CREATE TABLE IF NOT EXISTS blacklisted_guilds(
    guild_id BIGINT NOT NULL,
    PRIMARY KEY (guild_id)
);
-- A list of blacklisted guild IDs - the bot will auto-leave these guilds.


CREATE TABLE IF NOT EXISTS guild_specific_families(
    guild_id BIGINT NOT NULL,
    purchased_by BIGINT,
    PRIMARY KEY (guild_id)
);
-- A list of guild IDs of people who've paid for Gold.


DO $$ BEGIN
    CREATE TYPE direction AS ENUM ('TB', 'LR');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;
CREATE TABLE IF NOT EXISTS customisation(
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
-- A table for user tree customisations. The nulls are all set in the
-- bot's code for defaults.


CREATE TABLE IF NOT EXISTS blocked_user(
    user_id BIGINT,
    blocked_user_id BIGINT,
    PRIMARY KEY (user_id, blocked_user_id)
);
-- A user and a person they've blocked.


-- CREATE TABLE IF NOT EXISTS ship_percentages(
--     user_id_1 BIGINT,
--     user_id_2 BIGINT,
--     percentage SMALLINT,
--     PRIMARY KEY (user_id_1, user_id_2)
-- );
-- A list of set user pairs for the ship command, to override the
-- user ID calculation that it uses by default.
-- Commented out while we don't have the actual ship command added.


CREATE TABLE IF NOT EXISTS blog_posts(
    url VARCHAR(50) PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    body TEXT NOT NULL,
    created_at TIMESTAMP,
    author_id BIGINT
);
-- Markdown to render on the website.


CREATE TABLE IF NOT EXISTS redirects(
    code VARCHAR(50) PRIMARY KEY,
    location VARCHAR(2000)
);
-- Redirects from /r/{code} to the given location for the webiste.


CREATE TABLE IF NOT EXISTS disabled_commands(
    command_name VARCHAR(50) NOT NULL,
    guild_id BIGINT NOT NULL,
    disabled BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (command_name, guild_id)
);
-- Commands that are disabled for the bot, as specified in the website
-- settings. Can be removed when the message content intent is removed,
-- as users can manage this themselves via the slash command dashboard.


CREATE TABLE IF NOT EXISTS max_children_amount(
    guild_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    amount INTEGER DEFAULT 5,
    PRIMARY KEY (guild_id, role_id)
);
-- Max children count overrides for Gold to use, as specified in the
-- website settings.
