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

curl --location --request POST 'http://localhost:8000/biosamples/a39bc378-29a4-4e17-99c3-7ff5783fcde9/genomes/c06eb1b3-a80b-4e9e-aa55-e92ae4c0a0bc/upload' \
--form 'file=@"LL0772_assignedKin.fa.gz.gzi"'

### Database Integration

When files are uploaded, the system automatically:

- Creates a record in the `files` table with metadata
- Links genome files to genomes via `genome_files` table
- Creates annotation records and links them via `annotation_files` table

### MinIO Access

- MinIO Console: http://localhost:9001
- MinIO API: http://localhost:9000
- Default credentials: minioadmin / minioadmin123
