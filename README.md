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

curl --location --request POST 'http://localhost:8000/biosamples/a39bc378-29a4-4e17-99c3-7ff5783fcde9/genomes/f67ff84a-fc90-41df-9e16-4282d7568647/upload' \
--form 'file=@"UN0010_assignedKin.fa.gz.fai"'

### Database Integration

When files are uploaded, the system automatically:

- Creates a record in the `files` table with metadata
- Links genome files to genomes via `genome_files` table
- Creates annotation records and links them via `annotation_files` table

### MinIO Access

- MinIO Console: http://localhost:9001
- MinIO API: http://localhost:9000
- Default credentials: minioadmin / minioadmin123
