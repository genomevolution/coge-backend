# Comparative genomics API

## Run it

First, start the DB and MinIO

```sh
make start_db
```

Open another terminal and run the following

```sh
source .venv/bin/activate
```

```sh
source local.env
```

```sh
make run_server
```

## File Upload API

The API now supports file uploads for genomes and annotations using MinIO object storage.

### Endpoints

- `POST /biosamples/{biosampleId}/genomes/{genomeId}/upload` - Upload genome files (.fa, .fasta, .fna)
- `POST genomes/{genomeId}/annotations/{annotationId}/upload` - Upload annotation files (.gff3, .gff)
- `GET /files/download?filePath={path}` - Download files from MinIO
- `DELETE /files/delete?filePath={path}` - Delete files from MinIO

### File Organization

Files are organized in MinIO with the following structure:

- `{biosampleId}/genomes/{filename}` - for genome files
- `genomes/{genomeId}/annotations/{annotationId}/{filename}` - for annotation files

### Database Integration

When files are uploaded, the system automatically:

- Creates a record in the `files` table with metadata
- Links genome files to genomes via `genome_files` table
- Creates annotation records and links them via `annotation_files` table

### MinIO Access

- MinIO Console: http://localhost:9001
- MinIO API: http://localhost:9000
- Default credentials: minioadmin / minioadmin123
