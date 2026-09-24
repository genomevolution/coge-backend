# Comparative genomics API

## Run it

Run all services

```
make run-dev
```

Migrate

```
migrate-up
```

Create an asynchronous import

```bash
curl --request POST 'http://127.0.0.1:8000/imports/' \
  --form 'payload={"mode":"CREATE_ORGANISM","organism":{"name":"sample","taxId":"1","speciesName":"Example species"},"genome":{"name":"v1","description":"Assembly","accessionId":"GCA_1","sourceId":"SOURCE_ID","public":true}}' \
  --form 'fasta=@"genome.fa"'
```

The request returns `202 Accepted`. Poll `GET /imports/{importId}` until the
status is `PUBLISHED` or `ACTION_REQUIRED`.

Run a local BLAST search against public CoGe genomes:

```bash
curl --request POST 'http://127.0.0.1:8000/blast/jobs' \
  --header 'Content-Type: application/json' \
  --data '{"program":"blastn","query":">query\\nATGC","selection":{"mode":"IDS","genomeIds":["GENOME_ID"]},"parameters":{"evalue":1e-5,"maxTargetSeqs":50}}'
```

The request returns `202 Accepted`. Poll `GET /blast/jobs/{jobId}` while the job
is `QUEUED`, `PREPARING`, or `RUNNING`; retrieve completed hits with
`GET /blast/jobs/{jobId}/results` or download TSV with
`GET /blast/jobs/{jobId}/download`. Jobs and results expire after 48 hours.

Look up a canonical scientific name before importing with
`GET /taxonomy/{taxId}`. When a taxonomy already exists, the backend ignores a
submitted species spelling and uses the stored scientific name. A matching
organism name and taxid reuses that organism and publishes the sequencing as a
new genome; a different organism name may share the same taxonomy.
