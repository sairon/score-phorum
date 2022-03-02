demo:
	docker-compose -f docker-compose.yml up --build

dev:
	docker-compose -f docker-compose.yml up --scale phorum=0 --scale nginx=0

test:
	docker-compose -f docker-compose.test.yml up --build  --abort-on-container-exit --exit-code-from sut

.PHONY: dev test
