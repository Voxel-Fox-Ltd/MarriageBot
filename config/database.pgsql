CREATE TABLE guild_settings(
    guild_id BIGINT PRIMARY KEY,
    prefix VARCHAR(30)
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


CREATE TABLE paypal_purchases(
    id VARCHAR(64) NOT NULL PRIMARY KEY,
    customer_id VARCHAR(18),
    item_name VARCHAR(200) NOT NULL,
    option_selection VARCHAR(200),
    payment_amount INTEGER NOT NULL,
    discord_id BIGINT NOT NULL,
    guild_id BIGINT NOT NULL,
    completed BOOLEAN NOT NULL DEFAULT FALSE,
    checkout_complete_timestamp TIMESTAMP
);
