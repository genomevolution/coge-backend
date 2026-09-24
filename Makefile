## Usado
.PHONY: run-dev run-seeds run-prod stop-all logs-dev logs-prod clean clean-db create-migration list-migrations migrate-up migrate-down

run-dev:
	docker compose --profile dev up --build --force-recreate  -d

run-seeds:
	PGPASSWORD=dummy_password psql -h localhost -U coge -d comparative_genomics -f ./db/seeds/seeds.sql


run-prod:
	docker compose --profile prod up --build --force-recreate
	
stop-all:
	docker compose down

logs-dev:
	docker compose --profile dev logs -f

logs-prod:
	docker compose --profile prod logs -f

clean:
	docker compose down -v
	docker system prune -f

# Remove application data while keeping schemas, migrations, users, and sources.
clean-db:
	docker compose exec -T db psql -U coge -d comparative_genomics -v ON_ERROR_STOP=1 -c "TRUNCATE TABLE processing.imports, data_files.annotation_files, data_files.genome_files, processing.executions, organism_data.annotations, data_files.files, organism_data.genome, core.organism CASCADE;"

# Database migration commands using dbmate
create-migration:
	dbmate new $(name)

list-migrations:
	dbmate --env-file dbmate.env --migrations-dir ./db/migrations status

migrate-up:
	dbmate --env-file dbmate.env --migrations-dir ./db/migrations up

migrate-down:
	dbmate --env-file dbmate.env --migrations-dir ./db/migrations down
