-- migrate:up
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS organism_data;

CREATE TABLE auth.users ( 
    id VARCHAR(36) NOT NULL PRIMARY KEY 
);

CREATE TABLE core.organism (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    name VARCHAR(256) NOT NULL,
    user_fk VARCHAR(36) REFERENCES auth.users (id),
    tax_id VARCHAR(36) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ,
    species_name VARCHAR(256)
);

CREATE TABLE organism_data.source (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    name VARCHAR(256) NOT NULL
);

CREATE TABLE organism_data.genome (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    organism_fk VARCHAR(36) NOT NULL REFERENCES core.organism (id),
    created_at TIMESTAMPTZ,
    name VARCHAR(256),
    description VARCHAR(1024),
    public BOOLEAN,
    accesion_id VARCHAR(256),
    source_fk VARCHAR(36) REFERENCES organism_data.source (id)
);

-- migrate:down
DROP TABLE IF EXISTS organism_data.genome;
DROP TABLE IF EXISTS organism_data.source;
DROP TABLE IF EXISTS core.organism;
DROP TABLE IF EXISTS auth.users;
DROP SCHEMA IF EXISTS organism_data CASCADE;
DROP SCHEMA IF EXISTS core CASCADE;
DROP SCHEMA IF EXISTS auth CASCADE;
