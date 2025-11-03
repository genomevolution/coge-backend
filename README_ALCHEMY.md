# SQLAlchemy Models - Documentation

## Overview

Los modelos SQLAlchemy proporcionan una forma elegante de interactuar con la base de datos usando ORM (Object-Relational Mapping).

## Structure

```
model/
├── base_alchemy.py              # Base declarativa compartida
├── user_alchemy.py              # auth.users
├── organism_alchemy.py          # core.organism
├── source_alchemy.py            # organism_data.source
├── genome_alchemy.py            # organism_data.genome
├── annotation_alchemy.py        # organism_data.annotations
├── file_alchemy.py              # data_files.files
├── genomeFile_alchemy.py        # data_files.genome_files
└── annotationFile_alchemy.py    # data_files.annotation_files
```

## Usage Example

### Using getGenomeById

```python
from repository.genome import GenomeRepository
from repository.db import DB
from repository.dbConfig import DBConfig

# Setup
config = DBConfig()
db = DB(config)
genome_repo = GenomeRepository(db)

# Get genome with all relations
genome_data = genome_repo.getGenomeById("6e638b6b-6023-4bde-a76d-08350dd09955")

# Returns:
{
    "id": "6e638b6b-6023-4bde-a76d-08350dd09955",
    "createdAt": "2025-10-27T00:52:02.319698+00:00",
    "name": "v1",
    "description": "Genome assembly generated...",
    "public": true,
    "accesionId": "GCA_041682335.1",
    "organism": {
        "id": "7e21c66b-d10d-4418-a634-6df0a1796366",
        "name": "Sample organism",
        "taxId": "94edc173-a4e6-42af-8b81-889f2d67d45f",
        "metadata": {...},
        "createdAt": "2025-10-27T00:52:02.318598+00:00",
        "speciesName": "Species name"
    },
    "source": {
        "id": "...",
        "name": "NCBI"
    },
    "genomeFiles": [
        {
            "id": "...",
            "type": "FASTA",
            "file": {
                "id": "...",
                "path": "/path/to/file.fasta",
                "createdAt": "...",
                "updatedAt": "...",
                "metadata": {...}
            }
        }
    ],
    "annotations": [
        {
            "id": "...",
            "name": "Primary annotation",
            "description": "...",
            "public": true,
            "primaryAnnotation": true,
            "createdAt": "...",
            "files": [
                {
                    "id": "...",
                    "type": "GFF",
                    "file": {
                        "id": "...",
                        "path": "/path/to/annotation.gff",
                        "createdAt": "...",
                        "updatedAt": "...",
                        "metadata": {...}
                    }
                }
            ]
        }
    ]
}
```

## Key Features

### Lazy Loading Control

Las relaciones inversas usan `lazy='noload'` para evitar queries innecesarios:

- **OrganismAlchemy.genomes**: `lazy='noload'` - No carga genomas automáticamente
- **SourceAlchemy.genomes**: `lazy='noload'` - No carga genomas automáticamente
- **GenomeAlchemy relations**: Se cargan explícitamente con `joinedload`

### Circular Reference Prevention

Los métodos `to_dict()` tienen control granular para evitar referencias circulares:

```python
# Genome incluye organism, pero organism NO incluye genomes
genome.to_dict(include_organism=True)

# Organism incluye genomes, pero genomes NO incluyen organism
organism.to_dict(include_genomes=True)
```

### Explicit Loading with joinedload

El método `getGenomeById` usa `joinedload` para cargar explícitamente todas las relaciones necesarias en una sola query:

```python
genome = session.query(GenomeAlchemy)\
    .options(
        joinedload(GenomeAlchemy.organism),
        joinedload(GenomeAlchemy.source),
        joinedload(GenomeAlchemy.genome_files).joinedload(GenomeFileAlchemy.file),
        joinedload(GenomeAlchemy.annotations).joinedload(AnnotationAlchemy.annotation_files).joinedload(AnnotationFileAlchemy.file)
    )\
    .filter(GenomeAlchemy.id == id)\
    .first()
```

## Best Practices

1. **Siempre cerrar sesiones**: El método usa `try/finally` para garantizar que las sesiones se cierren.

2. **Usar joinedload explícitamente**: Para relaciones que necesitas, usa `joinedload` en lugar de confiar en lazy loading.

3. **Controlar serialización**: Usa parámetros en `to_dict()` para controlar qué incluir.

4. **Migraciones primero**: Las migraciones SQL son la fuente de verdad, los modelos SQLAlchemy solo reflejan la estructura.

## Migration Workflow

1. Crear migración SQL con dbmate
2. Aplicar migración: `dbmate up`
3. Actualizar modelos SQLAlchemy para reflejar cambios
4. Usar modelos para queries ORM

## Notes

- **NO usar** `Base.metadata.create_all()` - Las tablas ya existen por migraciones
- Las sesiones se crean por query y se cierran después
- El engine se reutiliza para todas las sesiones (singleton pattern)

