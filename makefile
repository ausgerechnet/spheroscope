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
