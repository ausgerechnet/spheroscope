# spheroscope #
spheroscope is a corpus viewer and analyzer. The backend is based on
the Concordance and Collocation Computer
([ccc](https://pypi.org/project/cwb-ccc/)), which runs anchored CQP
queries.


## set-up ##
We use `pipenv`. install necessary modules via

	pipenv install


Then switch to the virtual environment via

	pipenv shell


## configuration ##
You will need a CWB indexed corpus and word embeddings. Configure the
app via "spheroscope.cfg" in the [app](app/) folder. You can find an
[example config file](app/spheroscope_example.cfg) in the
repository. Your config should at least contain the lines
`REGISTRY_PATH`, `CORPUS_NAME`, and `CACHE_PATH`. 

You can use the `LIB_PATH` of the [stable
version](app/instance-stable/lib/). Additional fields are `EMBEDDINGS`
(which should point to a magnitude file) and `FILLFORM` (download the
latest version [here](https://gitlab.com/mgttlinger/fillform/-/jobs)).

## usage ##
start the app like so:

	./start-sterver.sh

and navigate to [http://127.0.0.1:5000/](http://127.0.0.1:5000/).
