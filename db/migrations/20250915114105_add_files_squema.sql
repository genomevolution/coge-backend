-- migrate:up
CREATE SCHEMA IF NOT EXISTS data_files;

CREATE TABLE data_files.files (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    path VARCHAR(256) NOT NULL,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    file_metadata JSONB
);

CREATE TABLE data_files.genome_files (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    file_fk VARCHAR(36) NOT NULL REFERENCES data_files.files (id),
    genome_fk VARCHAR(36) NOT NULL REFERENCES organism_data.genome (id),
    type VARCHAR(256) NOT NULL
);

CREATE TABLE organism_data.annotations (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    fk_genome VARCHAR(36) NOT NULL REFERENCES organism_data.genome (id),
    created_at TIMESTAMPTZ,
    name VARCHAR(256),
    description VARCHAR(1024),
    public BOOLEAN,
    primary_annotation BOOLEAN
);

CREATE TABLE data_files.annotation_files (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    file_fk VARCHAR(36) NOT NULL REFERENCES data_files.files (id),
    annotation_fk VARCHAR(36) NOT NULL REFERENCES organism_data.annotations (id),
    type VARCHAR(256) NOT NULL
);

-- migrate:down
DROP TABLE IF EXISTS data_files.annotation_files;
DROP TABLE IF EXISTS organism_data.annotations;
DROP TABLE IF EXISTS data_files.genome_files;
DROP TABLE IF EXISTS data_files.files;
DROP SCHEMA IF EXISTS data_files CASCADE;
