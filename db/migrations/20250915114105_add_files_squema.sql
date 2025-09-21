-- migrate:up

CREATE TABLE files (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    path VARCHAR(256) NOT NULL,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    file_metadata JSONB
);

CREATE TABLE genome_files (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    file_fk VARCHAR(36) NOT NULL REFERENCES files (id),
    genome_fk VARCHAR(36) NOT NULL REFERENCES genome (id),
    type VARCHAR(256) NOT NULL
);

CREATE TABLE annotations (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    fk_genome VARCHAR(36) NOT NULL REFERENCES genome (id),
    created_at TIMESTAMPTZ,
    name VARCHAR(256),
    description VARCHAR(1024),
    public BOOLEAN,
    primary_annotation BOOLEAN
);

CREATE TABLE annotation_files (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    file_fk VARCHAR(36) NOT NULL REFERENCES files (id),
    annotation_fk VARCHAR(36) NOT NULL REFERENCES annotations (id),
    type VARCHAR(256) NOT NULL
);          

-- migrate:down
DROP TABLE IF EXISTS files;
DROP TABLE IF EXISTS genome_files;
DROP TABLE IF EXISTS annotations;
DROP TABLE IF EXISTS annotation_files;
