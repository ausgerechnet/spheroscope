.PHONY: library

all: init run

install:
	pipenv install --dev

requirements:
	pipenv requirements > requirements.txt

clean:
	rm -rf *.egg-info build/ dist/


init:
	pipenv run flask --app spheroscope database init

library:
	pipenv run flask --app spheroscope database library


run:
	pipenv run flask --app spheroscope --debug run

query:
	pipenv run flask --app spheroscope query

subquery:
	pipenv run flask --app spheroscope subquery 3 1 24


results:
	pipenv run flask --app spheroscope --debug remote queries

patterns:
	pipenv run flask --app spheroscope --debug remote patterns

gold:
	pipenv run flask --app spheroscope --debug remote gold


