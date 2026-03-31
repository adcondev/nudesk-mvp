.PHONY: up down build test clean logs

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

test-go:
	cd gateway && go test ./...

test-py:
	# Add python testing commands here later
	@echo "Python tests not yet implemented"
