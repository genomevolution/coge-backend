-- migrate:up
CREATE INDEX taxonomy_scientific_name_prefix_idx
    ON core.taxonomy (lower(scientific_name) text_pattern_ops);
CREATE INDEX organism_name_prefix_idx
    ON core.organism (lower(name) text_pattern_ops);

-- migrate:down
DROP INDEX IF EXISTS core.organism_name_prefix_idx;
DROP INDEX IF EXISTS core.taxonomy_scientific_name_prefix_idx;
