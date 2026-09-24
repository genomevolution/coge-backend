-- migrate:up
CREATE INDEX taxonomy_tax_id_prefix_idx
    ON core.taxonomy (tax_id text_pattern_ops);

-- migrate:down
DROP INDEX IF EXISTS core.taxonomy_tax_id_prefix_idx;
