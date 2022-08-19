INSERT INTO usages(context_id, user_id, time) SELECT context_id, user_id, time FROM usages_old;
DROP TABLE usages_old;
