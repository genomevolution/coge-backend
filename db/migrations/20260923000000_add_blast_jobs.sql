-- migrate:up
CREATE TABLE processing.blast_jobs (
    id VARCHAR(36) PRIMARY KEY,
    program VARCHAR(32) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'QUEUED',
    progress INTEGER NOT NULL DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    query_fasta TEXT NOT NULL,
    selection JSONB NOT NULL,
    parameters JSONB NOT NULL DEFAULT '{}'::jsonb,
    execution_id VARCHAR(36),
    result_count INTEGER NOT NULL DEFAULT 0,
    results JSONB,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_blast_jobs_status_created ON processing.blast_jobs(status, created_at);
CREATE INDEX idx_blast_jobs_expires_at ON processing.blast_jobs(expires_at);

CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX idx_blast_genome_name_trgm
    ON organism_data.genome USING gin (name gin_trgm_ops);
CREATE INDEX idx_blast_genome_accession_trgm
    ON organism_data.genome USING gin (accesion_id gin_trgm_ops);
CREATE INDEX idx_blast_organism_name_trgm
    ON core.organism USING gin (name gin_trgm_ops);
CREATE INDEX idx_blast_organism_species_trgm
    ON core.organism USING gin (species_name gin_trgm_ops);
CREATE INDEX idx_blast_organism_tax_id
    ON core.organism (tax_id);

-- migrate:down
DROP TABLE IF EXISTS processing.blast_jobs;
DROP INDEX IF EXISTS idx_blast_genome_name_trgm;
DROP INDEX IF EXISTS idx_blast_genome_accession_trgm;
DROP INDEX IF EXISTS idx_blast_organism_name_trgm;
DROP INDEX IF EXISTS idx_blast_organism_species_trgm;
DROP INDEX IF EXISTS idx_blast_organism_tax_id;
