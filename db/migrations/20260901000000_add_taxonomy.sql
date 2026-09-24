-- migrate:up
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM core.organism
        WHERE tax_id !~ '^[0-9]+$' OR tax_id ~ '^0+$'
    ) THEN
        RAISE EXCEPTION 'Cannot create taxonomy: one or more taxids are not positive integers';
    END IF;

    UPDATE core.organism
    SET tax_id = (tax_id::NUMERIC)::TEXT;

    IF EXISTS (
        SELECT tax_id
        FROM core.organism
        GROUP BY tax_id
        HAVING COUNT(DISTINCT LOWER(BTRIM(species_name))) > 1
    ) THEN
        RAISE EXCEPTION 'Cannot create taxonomy: one or more taxids have conflicting species names';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM core.organism
        WHERE species_name IS NULL OR BTRIM(species_name) = ''
    ) THEN
        RAISE EXCEPTION 'Cannot create taxonomy: one or more organisms have no species name';
    END IF;
END $$;

CREATE TABLE core.taxonomy (
    tax_id VARCHAR(36) NOT NULL PRIMARY KEY,
    scientific_name VARCHAR(256) NOT NULL,
    parent_tax_id VARCHAR(36),
    rank VARCHAR(64),
    CONSTRAINT fk_taxonomy_parent
        FOREIGN KEY (parent_tax_id) REFERENCES core.taxonomy (tax_id)
        DEFERRABLE INITIALLY DEFERRED,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_taxonomy_parent_tax_id ON core.taxonomy (parent_tax_id);

INSERT INTO core.taxonomy (tax_id, scientific_name)
SELECT tax_id, MIN(BTRIM(species_name))
FROM core.organism
GROUP BY tax_id;

ALTER TABLE core.organism
    ADD CONSTRAINT fk_organism_taxonomy
    FOREIGN KEY (tax_id) REFERENCES core.taxonomy (tax_id);

CREATE UNIQUE INDEX uq_organism_name_tax_id
    ON core.organism (tax_id, LOWER(name));

-- migrate:down
DROP INDEX IF EXISTS core.uq_organism_name_tax_id;
ALTER TABLE core.organism DROP CONSTRAINT IF EXISTS fk_organism_taxonomy;
DROP TABLE IF EXISTS core.taxonomy;
