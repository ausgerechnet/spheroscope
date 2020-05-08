# spheroscope #
spheroscope is a corpus viewer and analyzer. The backend is based on
the Concordance and Collocation Computer
([CCC](https://github.com/ausgerechnet/cwb-ccc)), which runs anchored
CQPqueries.

## set-up ##
We use `pipenv`. Install necessary modules via

	pipenv install
	
and swith to an interactive shell:

	pipenv shell


## configuration ##
You will need a CWB indexed corpus and word embeddings for most of
what this app offers. Configure the app via "spheroscope.cfg" in the
[instance](instance/) folder. You can find an [example config
file](spheroscope_example.cfg) in the repository.

You can use the `LIB_PATH` of the [stable
instance](instance-stable/lib/).

`EMBEDDINGS` should point to a magnitude file.

Download the latest version of `FILLFORM`
[here](https://gitlab.com/mgttlinger/fillform/-/jobs)). Don't provide
this key if you do not want to use fillform.

Results will be written to and read from `RESULTS_PATH`. You can use
use one of the results of the [stable
instance](instance-stable/query-results/).

For the queries to run, you will have to provide a `CORPUS_NAME`, the
structural attribute where the meta identifier is stored in `S_META`
("tweet_id") and the structural attribute where to break your queries
("tweet").

The `CACHE_PATH` will be used to store temporary query results from
cwb-ccc.

## usage ##
Start the app like so:

	./start-sterver.sh

and navigate to [http://127.0.0.1:5000/](http://127.0.0.1:5000/).
