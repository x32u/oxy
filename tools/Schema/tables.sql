
CREATE TABLE IF NOT EXISTS authorize (
    guild_id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    till TIMESTAMP,
    transfers INT DEFAULT 2
);



CREATE TABLE IF NOT EXISTS prefixes (
    guild_id BIGINT PRIMARY KEY,
    prefix TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS afk (
    user_id BIGINT PRIMARY KEY,
    reason TEXT,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS autoroles (
    guild_id BIGINT PRIMARY KEY,
    role_id BIGINT
);

CREATE TABLE IF NOT EXISTS authorize (
    guild_id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    till TIMESTAMP,
    transfers INT DEFAULT 2
);


CREATE TABLE IF NOT EXISTS cache (
    key TEXT NOT NULL,
    value JSONB NOT NULL,
    PRIMARY KEY (key)
);


CREATE TABLE IF NOT EXISTS reskin (
    user_id BIGINT NOT NULL,
    username VARCHAR(32) NOT NULL,
    avatar_url TEXT,
    PRIMARY KEY (user_id)
);


CREATE TABLE IF NOT EXISTS reskin_enabled (
    guild_id BIGINT NOT NULL,
    PRIMARY KEY (guild_id)
);

CREATE TABLE IF NOT EXISTS force_nick (
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    nickname VARCHAR(32) NOT NULL,
    PRIMARY KEY (guild_id, user_id)
);


CREATE TABLE IF NOT EXISTS snipe_messages (
    id SERIAL PRIMARY KEY,
    author_id BIGINT NOT NULL,
    content TEXT,
    attachment_url TEXT,
    deleted_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    channel_id BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS edit_snipe_messages (
    id SERIAL PRIMARY KEY,
    author_id BIGINT NOT NULL,
    content TEXT,
    attachment_url TEXT,
    edited_at TIMESTAMP NOT NULL,
    channel_id BIGINT NOT NULL,
    before_content TEXT,
    after_content TEXT
);

CREATE TABLE IF NOT EXISTS warnings (
    id SERIAL PRIMARY KEY,
    guild_id VARCHAR(20) NOT NULL,
    user_id VARCHAR(20) NOT NULL,
    moderator_id VARCHAR(20) NOT NULL,
    reason TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS lockdown_ignore (
    guild_id VARCHAR(20) NOT NULL,
    channel_id VARCHAR(20) NOT NULL,
    PRIMARY KEY (guild_id, channel_id)
);

CREATE TABLE IF NOT EXISTS lock_role (
    guild_id VARCHAR(20) PRIMARY KEY,
    role_id VARCHAR(20) NOT NULL
);

CREATE TABLE IF NOT EXISTS voicemaster (
    guild_id BIGINT PRIMARY KEY,
    channel_id BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS vcs (
    user_id BIGINT NOT NULL,
    voice BIGINT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS lastfm (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    customcmd VARCHAR(255),
    embed TEXT,
    reactions JSONB
);

CREATE TABLE IF NOT EXISTS lastfm_usernames (
    user_id BIGINT PRIMARY KEY,
    username TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cashapp (
    user_id BIGINT PRIMARY KEY,
    cashapp_username VARCHAR(255)
);