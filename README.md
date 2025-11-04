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

Run migrations



curl --location --request POST 'http://127.0.0.1:8000/organisms/4ba32111-dced-4cf0-9837-3d85dd8321fc/genomes/6e638b6b-6023-4bde-a76d-08350dd09955/upload' --form 'file=@"LL0772_assignedKin.fa"'