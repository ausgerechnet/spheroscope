# spheroscope #

spheroscope is a corpus viewer and analyzer. The backend is based on
[cwb-ccc](https://pypi.org/project/cwb-ccc/), which runs multiply
anchored CQP queries.

## Setup ##
We use `pipenv` for dependency management. Install `pipenv` via `pip`:
	
	pip install -r requirements.txt

`pipenv` takes care of the rest:

	pipenv install --dev
	
Switch to an interactive shell via

	pipenv shell

## Configuration ##
You will need a CWB indexed corpus and word embeddings for most of
what this app offers. Configure the app via `spheroscope.cfg`. You can
find an [example config file](spheroscope_example.cfg) in the
repository.

Set the `REGISTRY_PATH` to your CWB registry and `CACHE_PATH` to some
directory where you have access (e.\,g. `/tmp/spheroscope`).

Link to a stable version of
[fillform](https://gitlab.com/mgttlinger/fillform/-/jobs) via
`FILLFORM`. Don't provide this key if you do not want to use fillform.

You can then run

	./init.sh
	
to populate your local instance with all queries, macros, and
wordlists from the [library](library/).

You can now start the flask server via

	./start-server.sh

and navigate to [http://127.0.0.1:5000/](http://127.0.0.1:5000/) to
access the interface.

## Corpus Settings ##
After starting the app, you will find [default corpus
settings](instance/corpus_defaults.cfg) in your instance folder.

When selecting one of your system corpora for the first time through
the interface, a new folder and config file will be created for this
corpus in your instance folder. You should point the `embeddings`
parameter to appropriate embeddings stored as `pymagnitude` files.

# Usage

TBD
