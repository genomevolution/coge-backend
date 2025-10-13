INSERT INTO users (id) VALUES ('USER-UUID');

INSERT INTO
    organism (
        id,
        name,
        user_fk,
        tax_id,
        metadata,
        created_at,
        species_name
    )
VALUES (
        'ORGANISM-UUID1',
        'Organism 1',
        'USER-UUID',
        'TAX-UUID',
        '{"hello":"world"}',
        '2016-01-25T10:10:10.555555',
        'Organism 1 specie'
    );

INSERT INTO
    genome (
        id,
        organism_fk,
        prefix,
        created_at,
        name,
        description,
        public,
        accesion_id
    )
VALUES (
        'GENOME-UUID1',
        'ORGANISM-UUID1',
        'GENOME-PREFIX',
        '2016-01-25T10:10:10.555555',
        'Genome 1',
        'This is a genome description',
        true,
        'ACCESION_ID'
    );

INSERT INTO
    organism (
        id,
        name,
        user_fk,
        tax_id,
        metadata,
        created_at,
        species_name
    )
VALUES (
        'ORGANISM-UUID2',
        'Organism 2',
        'USER-UUID',
        'TAX-UUID2',
        '{"hello":"world"}',
        '2016-01-25T10:10:10.555555',
        'Organism 2 specie'
    );

INSERT INTO
    organism (
        id,
        name,
        user_fk,
        tax_id,
        metadata,
        created_at,
        species_name
    )
VALUES (
        'ORGANISM-UUID3',
        'Organism 3',
        'USER-UUID',
        'TAX-UUID3',
        '{"hello":"world"}',
        '2016-01-25T10:10:10.555555',
        'Organism 3 specie'
    );

INSERT INTO
    organism (
        id,
        name,
        user_fk,
        tax_id,
        metadata,
        created_at,
        species_name
    )
VALUES (
        'ORGANISM-UUID4',
        'Organism 4',
        'USER-UUID',
        'TAX-UUID4',
        '{"hello":"world"}',
        '2016-01-25T10:10:10.555555',
        'Organism 4 specie'
    );

INSERT INTO
    organism (
        id,
        name,
        user_fk,
        tax_id,
        metadata,
        created_at,
        species_name
    )
VALUES (
        'ORGANISM-UUID5',
        'Organism 5',
        'USER-UUID',
        'TAX-UUID5',
        '{"hello":"world"}',
        '2016-01-25T10:10:10.555555',
        'Organism 5 specie'
    );

INSERT INTO
    organism (
        id,
        name,
        user_fk,
        tax_id,
        metadata,
        created_at,
        species_name
    )
VALUES (
        'ORGANISM-UUID6',
        'Organism 6',
        'USER-UUID',
        'TAX-UUID6',
        '{"hello":"world"}',
        '2016-01-25T10:10:10.555555',
        'Organism 6 specie'
    );

INSERT INTO
    genome (
        id,
        organism_fk,
        prefix,
        created_at,
        name,
        description,
        public,
        accesion_id
    )
VALUES (
        'GENOME-UUID2',
        'ORGANISM-UUID2',
        'GENOME-PREFIX',
        '2016-01-25T10:10:10.555555',
        'Genome 2',
        'This is a genome description',
        true,
        'ACCESION_ID2'
    );

INSERT INTO
    genome (
        id,
        organism_fk,
        prefix,
        created_at,
        name,
        description,
        public,
        accesion_id
    )
VALUES (
        'GENOME-UUID3',
        'ORGANISM-UUID3',
        'GENOME-PREFIX',
        '2016-01-25T10:10:10.555555',
        'Genome 3',
        'This is a genome description',
        true,
        'ACCESION_ID3'
    );

INSERT INTO
    genome (
        id,
        organism_fk,
        prefix,
        created_at,
        name,
        description,
        public,
        accesion_id
    )
VALUES (
        'GENOME-UUID4',
        'ORGANISM-UUID4',
        'GENOME-PREFIX',
        '2016-01-25T10:10:10.555555',
        'Genome 4',
        'This is a genome description',
        true,
        'ACCESION_ID4'
    );

INSERT INTO
    genome (
        id,
        organism_fk,
        prefix,
        created_at,
        name,
        description,
        public,
        accesion_id
    )
VALUES (
        'GENOME-UUID5',
        'ORGANISM-UUID5',
        'GENOME-PREFIX',
        '2016-01-25T10:10:10.555555',
        'Genome 5',
        'This is a genome description',
        true,
        'ACCESION_ID5'
    );

INSERT INTO
    genome (
        id,
        organism_fk,
        prefix,
        created_at,
        name,
        description,
        public,
        accesion_id
    )
VALUES (
        'GENOME-UUID6',
        'ORGANISM-UUID6',
        'GENOME-PREFIX',
        '2016-01-25T10:10:10.555555',
        'Genome 6',
        'This is a genome description',
        true,
        'ACCESION_ID6'
    );

INSERT INTO
    annotations (
        id,
        fk_genome,
        created_at,
        name,
        description,
        public,
        primary_annotation
    )
VALUES (
        'ANNOTATION-UUID1',
        'GENOME-UUID1',
        '2025-09-21 19:35:05.238279+00',
        'Annotation for test_annotation.gff3',
        'Annotation file uploaded: test_annotation.gff3',
        true,
        false
    );

INSERT INTO
    annotations (
        id,
        fk_genome,
        created_at,
        name,
        description,
        public,
        primary_annotation
    )
VALUES (
        'ANNOTATION-UUID2',
        'GENOME-UUID1',
        '2025-09-21 19:35:05.238279+00',
        'Annotation for test_annotation.gff3',
        'Annotation file uploaded: test_annotation.gff3',
        true,
        false
    );
