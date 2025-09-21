INSERT INTO users (id) VALUES ('USER-UUID');

INSERT INTO
    biosample (
        id,
        name,
        user_fk,
        tax_id,
        metadata,
        created_at,
        species_name
    )
VALUES (
        'BIOSAMPLE-UUID1',
        'Biosample 1',
        'USER-UUID',
        'TAX-UUID',
        '{"hello":"world"}',
        '2016-01-25T10:10:10.555555',
        'Biosample 1 specie'
    );

INSERT INTO
    genome (
        id,
        biosample_fk,
        prefix,
        created_at,
        name,
        description,
        public,
        accesion_id
    )
VALUES (
        'GENOME-UUID1',
        'BIOSAMPLE-UUID1',
        'GENOME-PREFIX',
        '2016-01-25T10:10:10.555555',
        'Genome 1',
        'This is a genome description',
        true,
        'ACCESION_ID'
    );

INSERT INTO
    biosample (
        id,
        name,
        user_fk,
        tax_id,
        metadata,
        created_at,
        species_name
    )
VALUES (
        'BIOSAMPLE-UUID2',
        'Biosample 2',
        'USER-UUID',
        'TAX-UUID2',
        '{"hello":"world"}',
        '2016-01-25T10:10:10.555555',
        'Biosample 2 specie'
    );

INSERT INTO
    biosample (
        id,
        name,
        user_fk,
        tax_id,
        metadata,
        created_at,
        species_name
    )
VALUES (
        'BIOSAMPLE-UUID3',
        'Biosample 3',
        'USER-UUID',
        'TAX-UUID3',
        '{"hello":"world"}',
        '2016-01-25T10:10:10.555555',
        'Biosample 3 specie'
    );

INSERT INTO
    biosample (
        id,
        name,
        user_fk,
        tax_id,
        metadata,
        created_at,
        species_name
    )
VALUES (
        'BIOSAMPLE-UUID4',
        'Biosample 4',
        'USER-UUID',
        'TAX-UUID4',
        '{"hello":"world"}',
        '2016-01-25T10:10:10.555555',
        'Biosample 4 specie'
    );

INSERT INTO
    biosample (
        id,
        name,
        user_fk,
        tax_id,
        metadata,
        created_at,
        species_name
    )
VALUES (
        'BIOSAMPLE-UUID5',
        'Biosample 5',
        'USER-UUID',
        'TAX-UUID5',
        '{"hello":"world"}',
        '2016-01-25T10:10:10.555555',
        'Biosample 5 specie'
    );

INSERT INTO
    biosample (
        id,
        name,
        user_fk,
        tax_id,
        metadata,
        created_at,
        species_name
    )
VALUES (
        'BIOSAMPLE-UUID6',
        'Biosample 6',
        'USER-UUID',
        'TAX-UUID6',
        '{"hello":"world"}',
        '2016-01-25T10:10:10.555555',
        'Biosample 6 specie'
    );

INSERT INTO
    genome (
        id,
        biosample_fk,
        prefix,
        created_at,
        name,
        description,
        public,
        accesion_id
    )
VALUES (
        'GENOME-UUID2',
        'BIOSAMPLE-UUID2',
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
        biosample_fk,
        prefix,
        created_at,
        name,
        description,
        public,
        accesion_id
    )
VALUES (
        'GENOME-UUID3',
        'BIOSAMPLE-UUID3',
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
        biosample_fk,
        prefix,
        created_at,
        name,
        description,
        public,
        accesion_id
    )
VALUES (
        'GENOME-UUID4',
        'BIOSAMPLE-UUID4',
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
        biosample_fk,
        prefix,
        created_at,
        name,
        description,
        public,
        accesion_id
    )
VALUES (
        'GENOME-UUID5',
        'BIOSAMPLE-UUID5',
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
        biosample_fk,
        prefix,
        created_at,
        name,
        description,
        public,
        accesion_id
    )
VALUES (
        'GENOME-UUID6',
        'BIOSAMPLE-UUID6',
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
