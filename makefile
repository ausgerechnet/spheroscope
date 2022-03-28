all: init run

install:
	pip3 install -r requirements.txt
	pipenv install --dev

init:
	export FLASK_APP=spheroscope && \
	export FLASK_ENV=development && \
	pipenv run flask init-db && \
	pipenv run flask import-lib

run:
	export FLASK_APP=spheroscope && \
	export FLASK_ENV=development && \
	pipenv run flask run

subquery:
	export FLASK_APP=spheroscope && \
	export FLASK_ENV=development && \
	pipenv run flask subquery 3 1 24

query:
	export FLASK_APP=spheroscope && \
	export FLASK_ENV=development && \
	pipenv run flask query

patterns:
	export FLASK_APP=spheroscope && \
	export FLASK_ENV=development && \
	pipenv run flask update-patterns

gold:
	export FLASK_APP=spheroscope && \
	export FLASK_ENV=development && \
	pipenv run flask update-gold

clean:
	rm -rf *.egg-info build/ dist/
