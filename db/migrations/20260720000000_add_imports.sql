-- migrate:up
CREATE TABLE processing.imports (
    id VARCHAR(36) PRIMARY KEY,
    mode VARCHAR(32) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'QUEUED',
    phase VARCHAR(64) NOT NULL DEFAULT 'QUEUED',
    progress INTEGER NOT NULL DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    payload JSONB NOT NULL,
    target_organism_id VARCHAR(36) REFERENCES core.organism(id),
    planned_organism_id VARCHAR(36),
    planned_genome_id VARCHAR(36),
    planned_annotation_id VARCHAR(36),
    fasta_path TEXT,
    gff3_path TEXT,
    current_execution_id VARCHAR(36),
    current_execution_type VARCHAR(64),
    execution_metadata JSONB,
    failed_component VARCHAR(32),
    error_message TEXT,
    published_entity_id VARCHAR(36),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_imports_status ON processing.imports(status);
CREATE INDEX idx_imports_created_at ON processing.imports(created_at DESC);
CREATE INDEX idx_imports_target_organism ON processing.imports(target_organism_id);

-- migrate:down
DROP TABLE IF EXISTS processing.imports;
