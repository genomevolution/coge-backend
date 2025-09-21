-- migrate:up
CREATE TABLE users ( id VARCHAR(36) NOT NULL PRIMARY KEY );

CREATE TABLE biosample (
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
    biosample_fk VARCHAR(36) NOT NULL REFERENCES biosample (id),
    prefix VARCHAR(36) NOT NULL,
    created_at TIMESTAMPTZ,
    name VARCHAR(256),
    description VARCHAR(1024),
    public BOOLEAN,
    accesion_id VARCHAR(256)
);

-- migrate:down
DROP TABLE IF EXISTS genome;

DROP TABLE IF EXISTS biosample;

DROP TABLE IF EXISTS users;
