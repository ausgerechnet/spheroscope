# spheroscope #

spheroscope is a corpus viewer and analyzer. The backend is based on
[cwb-ccc](https://pypi.org/project/cwb-ccc/), which runs multiply
anchored CQP queries.

## Prerequisites ##
You will need a working installation of the [IMS Open Corpus Workbench
(CWB)](http://cwb.sourceforge.net/), a CWB-indexed corpus, as well as
word embeddings for most of what this app offers. The python3
dependencies will be installed automatically if you follow the setup
guide below.

## Setup ##
We use `pipenv` for dependency management. Install `pipenv` via `pip`:
	
	pip install -r requirements.txt

`pipenv` takes care of the rest:

	pipenv install --dev
	
Don't forget to switch to an interactive shell via

	pipenv shell

Alternatively, you can can configure an anaconda environment using the
additional [requirements file](requirements_anaconda.txt).

## Configuration ##
Configure the app via `spheroscope.cfg`. You can find an [example
config file](spheroscope_example.cfg) in the repository.

Set the `REGISTRY_PATH` to your CWB registry and `CACHE_PATH` to some
directory where you have appropriate rights (e.g. `/tmp/spheroscope`).

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
settings](instance/corpus_defaults.cfg) in your instance folder. You
can change these to your liking, taking into consideration the most
common p- and s-attributes of your system corpora.

When selecting one of your corpora for the first time through the
interface, a new folder and config file will be created for this
corpus in your instance folder; the config file will be populated with
the corpus defaults. If you want to use similarity-based
recommendations for wordlists, you should point the `embeddings`
parameter to appropriate embeddings stored as `pymagnitude` files. The
`query` and `display` settings can be change through the interface
(http://127.0.0.1:5000/corpora/).

# Usage

TBD
