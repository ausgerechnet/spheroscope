# spheroscope #
spheroscope is a corpus viewer and analyzer. The backend is based on
the Concordance and Collocation Computer
([CCC](https://gitlab.cs.fau.de/pheinrich/ccc)), which runs anchored
CQPqueries.

## set-up ##
We use `pipenv`. install necessary modules via
```
./env-setup.sh
```

For running CQP queries (the default on the master branch), you will
have to download and install the CCC module separately via

```
pipenv install /path/to/CCC/
```

## configuration ##
You will need a CWB indexed corpus and word embeddings. Configure the
app via "spheroscope.cfg" in the [app](app/) folder. You can find an
[example config file](app/spheroscope_example.cfg) in the
repository. Your config should at least contain the lines
`REGISTRY_PATH` and `CORPUS_NAME`. You can use the `LIB_PATH` of the
[stable version](app/instance-stable/lib/). Additional fields are
`EMBEDDINGS` and `FILLFORM`.

## usage ##
start the app like so:

```
./start-sterver.sh
```

and navigate to [http://127.0.0.1:5000/](http://127.0.0.1:5000/).
```
