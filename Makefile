run-dev:
	docker compose --profile dev up --build

run-prod:
	docker compose --profile prod up --build
	
stop-all:
	docker compose down

logs-dev:
	docker compose --profile dev logs -f

logs-prod:
	docker compose --profile prod logs -f

clean:
	docker compose down -v
	docker system prune -f

# Database migration commands using dbmate
create-migration:
	dbmate new $(name)

list-migrations:
	dbmate --env-file dbmate.env --migrations-dir ./db/migrations status

migrate-up:
	dbmate --env-file dbmate.env --migrations-dir ./db/migrations up

migrate-down:
	dbmate --env-file dbmate.env --migrations-dir ./db/migrations down

run-seeds:
	PGPASSWORD=dummy_password psql -h localhost -U coge -d comparative_genomics -f ./db/seeds/seeds.sql
