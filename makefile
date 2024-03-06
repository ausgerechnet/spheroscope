.PHONY: library



install:
	pipenv install --dev

requirements:
	pipenv requirements > requirements.txt

clean:
	rm -rf *.egg-info build/ dist/



init:
	pipenv run flask --app spheroscope --debug database init

library:
	pipenv run flask --app spheroscope --debug database library



run:
	pipenv run flask --app spheroscope --debug run



query:
	pipenv run flask --app spheroscope --debug patterns query --pattern 24

subquery:
	pipenv run flask --app spheroscope --debug patterns subquery 3 1 24




results:
	pipenv run flask --app spheroscope --debug remote queries

patterns:
	pipenv run flask --app spheroscope --debug remote patterns

gold:
	pipenv run flask --app spheroscope --debug remote gold

tweetsets:
	pipenv run flask --app spheroscope --debug remote tweetsets


docker-build:
	docker build --rm -t spheroscope -f Dockerfile .

docker-run:
	docker run -t --network host --name spheroscope --rm spheroscope
