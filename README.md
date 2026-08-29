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
