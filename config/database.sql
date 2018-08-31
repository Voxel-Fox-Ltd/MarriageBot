DROP DATABASE IF EXISTS marriagebot;
CREATE DATABASE marriagebot;
USE marriagebot;


CREATE TABLE marriages(
    marriage_id VARCHAR(11) NOT NULL,
    user_id BIGINT NOT NULL,
    partner_id BIGINT NOT NULL,
    valid BOOLEAN NOT NULL,
    PRIMARY KEY (marriage_id, user_id)
);
-- This table will hold marraiges both in date and divorced pairs
-- marriage_id will be a random 11-character string
-- user_id will be one of the users involved (the other user will get an entry with an identical marriage_id)


CREATE TABLE parents(
    child_id BIGINT NOT NULL,
    parent_id BIGINT NOT NULL,
    PRIMARY KEY (child_id)
);
-- Since a child will only appear once, you can set child_id to the primary key
-- A parent can have many children, a child will have only one parent


CREATE TABLE blacklisted_guilds(
    guild_id BIGINT NOT NULL,
    PRIMARY KEY (guild_id)
);
-- Basically a big ol' list of blacklisted guild IDs
