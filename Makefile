demo:
	docker-compose -f docker-compose.yml up --build

dev:
	docker-compose -f docker-compose.yml up --scale phorum=0 --scale nginx=0

docker-build:
	docker build -t sairon/score-phorum:latest .

docker-publish: docker-build
	docker push sairon/score-phorum:latest

test:
	docker compose -f docker-compose.test.yml up --build  --abort-on-container-exit --exit-code-from sut

# Code quality commands
ruff:
	ruff check src/

ruff-fix:
	ruff check --fix src/

ruff-format:
	ruff format src/

ruff-format-check:
	ruff format --check src/

pre-commit:
	pre-commit run --all-files

pre-commit-install:
	pre-commit install

.PHONY: demo dev docker-build docker-publish test ruff ruff-fix ruff-format ruff-format-check pre-commit pre-commit-install
