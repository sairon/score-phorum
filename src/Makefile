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

sass:
	@$(COMPASS_CMD) \
	    bundler install && \
	    cd phorum/static && \
	    compass compile

serve: migrate
	$(SERVE_CMD)

wait-for-db:
	@while ! nc -z $$PHORUM_DB_HOST 5432; \
	do \
	  echo "Waiting for DB server @ $$PHORUM_DB_HOST:5432..."; \
	  sleep 1; \
	done; \

.PHONY: collectstatic manage.py migrate sass serve wait-for-db
