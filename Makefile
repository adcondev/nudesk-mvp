.PHONY: up down build test test-go test-py test-e2e migrate lint clean logs

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

clean: down
	docker compose down -v
	rm -rf data/uploads/*

test: test-go test-py

test-go:
	cd gateway && go test ./...

test-py:
	pytest services/ tests/ -v

test-e2e:
	pytest tests/integration/ -v

migrate:
	docker compose exec extraction alembic upgrade head

lint:
	cd gateway && go vet ./...
	ruff check services/
