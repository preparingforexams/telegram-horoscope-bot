-- Move legacy out of the way
ALTER TABLE usages RENAME TO usages_old;
DROP INDEX usages_by_ids;
