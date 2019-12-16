# spheroscope #
spheroscope is a corpus viewer and analyzer. The backend is based on
the Concordance and Collocation Computer
[(CCC)]([https://gitlab.cs.fau.de/pheinrich/ccc]), which runs anchored
CQPqueries.

## requirements ##
You will need a CWB indexed corpus and word embeddings. Configure the
app via the [config file](app/instance/spheroscope.cfg).

## set-up ##
We use `pipenv`. install necessary modules via
```
./env-setup.sh
```

For running CQP queries (the default on the master branch), you will
have to install the CCC module separately.

## flask server ##
start the app like so:

```
./start-sterver.sh
```

## current modules ##
app/spheroscope/db.py
app/spheroscope/word_lists.py
app/spheroscope/queries.py
