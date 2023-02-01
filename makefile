all: init run

install:
	pipenv install --dev

requirements:
	pipenv requirements > requirements.txt

init:
	pipenv run flask --app spheroscope init-db

library:
	pipenv run flask --app spheroscope import-lib

run:
	pipenv run flask --app spheroscope --debug run

query:
	pipenv run flask --app spheroscope query

subquery:
	pipenv run flask --app spheroscope subquery 3 1 24

patterns:
	pipenv run flask --app spheroscope --debug update-patterns

gold:
	pipenv run flask --app spheroscope --debug update-gold

clean:
	rm -rf *.egg-info build/ dist/
