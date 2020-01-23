# spheroscope #
spheroscope is a corpus viewer and analyzer. The backend is based on
the Concordance and Collocation Computer
([CCC](https://gitlab.cs.fau.de/pheinrich/ccc)), which runs anchored
CQPqueries.

## requirements ##
You will need a CWB indexed corpus and word embeddings. Configure the
app via the [config file](spheroscope.cfg), which has to be put into
the [app](app/) folder.

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

## flask server ##
start the app like so:

```
./start-sterver.sh
```

## current modules ##
