activate_venv:
	source .venv/bin/activate

upgrade_pip:
	python -m pip install --upgrade pip

install_fast_api:
	pip install "fastapi[standard]"

install_postgres:
	pip install psycopg2-binary

run_server:
	fastapi dev main.py

start_db:
	docker compose up db
