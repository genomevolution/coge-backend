-- migrate:up
-- Create schema for processing jobs
CREATE SCHEMA IF NOT EXISTS processing;

-- Create processing_executions table to track Nextflow pipeline executions
CREATE TABLE processing.executions (
    id VARCHAR(36) PRIMARY KEY,
    genome_id VARCHAR(36) REFERENCES organism_data.genome(id) ON DELETE CASCADE,
    execution_type VARCHAR(50) NOT NULL DEFAULT 'GENOME_INDEXING',
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    pid INTEGER,
    profile VARCHAR(50),
    fasta_path TEXT,
    output_dir TEXT,
    log_file TEXT,
    error_message TEXT,
    execution_metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX idx_executions_genome_id ON processing.executions(genome_id);
CREATE INDEX idx_executions_status ON processing.executions(status);
CREATE INDEX idx_executions_created_at ON processing.executions(created_at DESC);
CREATE INDEX idx_executions_type_status ON processing.executions(execution_type, status);

-- Add comment to table
COMMENT ON TABLE processing.executions IS 'Tracks Nextflow pipeline executions for genome processing tasks';
COMMENT ON COLUMN processing.executions.status IS 'Execution status: PENDING, RUNNING, COMPLETED, FAILED, CANCELLED';
COMMENT ON COLUMN processing.executions.execution_type IS 'Type of processing: GENOME_INDEXING, ANNOTATION_PROCESSING, etc.';
COMMENT ON COLUMN processing.executions.progress IS 'Execution progress from 0 to 100';

-- migrate:down
DROP TABLE IF EXISTS processing.executions;
DROP SCHEMA IF EXISTS processing CASCADE;

