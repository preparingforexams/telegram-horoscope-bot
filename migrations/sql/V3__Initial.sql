CREATE TABLE usages (
    context_id TEXT,
    user_id TEXT,
    time INT NOT NULL,
    reference_id TEXT,
    PRIMARY KEY (context_id, user_id, time)
);
CREATE INDEX usages_by_ids on usages (
    context_id,
    user_id,
    time DESC
);
