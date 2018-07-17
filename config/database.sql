DROP DATABASE IF EXISTS marriagebot;
CREATE DATABASE marriagebot;
USE marriagebot;


CREATE TYPE event AS ENUM (
    'MARRIAGE', 'DIVORCE', 'PROPOSAL', 'I DO', 'I DONT', 'ALREADY MARRIED', 'TIMEOUT'
);


CREATE TABLE marriages(
    marriage_id VARCHAR(11) NOT NULL,
    user_id BIGINT NOT NULL,
    user_name VARCHAR(36) NOT NULL,
    partner_id BIGINT NOT NULL,
    partner_name VARCHAR(36) NOT NULL,
    valid BOOLEAN NOT NULL,
    PRIMARY KEY (marriage_id, user_id)
);
-- This table will hold marraiges both in date and divorced pairs
-- marriage_id will be a random 11-character string
-- user_id will be one of the users involved (the other user will get an entry with an identical marriage_id)


CREATE TABLE events(
    event_id VARCHAR(11) NOT NULL,
    event_type event NOT NULL,
    instigator BIGINT NOT NULL,
    target BIGINT NOT NULL,
    time TIMESTAMP NOT NULL,
    PRIMARY KEY (event_id)
);
-- This table bears no effect on the actual running of the bot, but is rather for diagnostics
-- instigator is the person who triggered the event 
-- target is the person who the event is triggered in favour of (ie who they proposed to or who they declined)
-- In the event of a marriage an entry is made for each user in the partnership
-- event_id is a random 11-character string
-- time is when the event was triggered
