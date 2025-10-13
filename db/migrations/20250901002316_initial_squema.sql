-- migrate:up
CREATE TABLE users ( id VARCHAR(36) NOT NULL PRIMARY KEY );

CREATE TABLE organism (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    name VARCHAR(256) NOT NULL,
    user_fk VARCHAR(36) REFERENCES users (id),
    tax_id VARCHAR(36) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ,
    species_name VARCHAR(256)
);

CREATE TABLE genome (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    organism_fk VARCHAR(36) NOT NULL REFERENCES organism (id),
    prefix VARCHAR(36) NOT NULL,
    created_at TIMESTAMPTZ,
    name VARCHAR(256),
    description VARCHAR(1024),
    public BOOLEAN,
    accesion_id VARCHAR(256)
);

-- migrate:down
DROP TABLE IF EXISTS genome;

DROP TABLE IF EXISTS organism;

DROP TABLE IF EXISTS users;
