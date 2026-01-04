SERVE_CMD := uwsgi --socket 0.0.0.0:8000 --chdir /srv/app --uid 33 --gid 33 --wsgi-file score/wsgi.py --master --processes 5 --stats 0.0.0.0:8001 --reload-on-rss 60

collectstatic:
	@[ -d ./static ] || mkdir static
	@python manage.py collectstatic --noinput

manage.py:
ifndef ARG
	$(error Usage: make manage.py ARG='...')
endif
	@python manage.py $(ARG)

migrate: wait-for-db
	@python manage.py migrate

define node_container
	docker run --rm $(1) --user $(shell id -u):$(shell id -g) \
		-v $(PWD):/app \
		-w /app \
		node:24-slim \
		sh -c "$(2)"
endef

sass:
	$(call node_container,,npm ci --cache /tmp/.npm && npm run sass)

sass-watch:
	$(call node_container,-it,npm ci --cache /tmp/.npm && npm run sass:watch)

# use as `make with-node` to run interactive shell
# or `make with-node CMD='command'` to run a specific command
with-node:
	$(call node_container,-it,$(or $(CMD),sh))

serve: migrate
	$(SERVE_CMD)

test: wait-for-db
	@python manage.py test

wait-for-db:
	@while ! nc -z $$PHORUM_DB_HOST 5432; \
	do \
	  echo "Waiting for DB server @ $$PHORUM_DB_HOST:5432..."; \
	  sleep 1; \
	done; \

.PHONY: collectstatic manage.py migrate sass sass-watch serve test wait-for-db with-node
