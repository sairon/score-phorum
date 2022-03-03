demo:
	docker-compose -f docker-compose.yml up --build

dev:
	docker-compose -f docker-compose.yml up --scale phorum=0 --scale nginx=0

docker-build:
	docker build -t sairon/score-phorum:latest .

docker-publish: docker-build
	docker push sairon/score-phorum:latest

test:
	docker-compose -f docker-compose.test.yml up --build  --abort-on-container-exit --exit-code-from sut

.PHONY: demo dev docker-build docker-publish test
