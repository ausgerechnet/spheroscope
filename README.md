# spheroscope #
spheroscope is a corpus viewer and analyzer. The backend is based on
the [Concordance and Collocation Computer
(CCC)]([https://gitlab.cs.fau.de/pheinrich/ccc]), which runs anchored CQP
queries. 

## requirements ##
You will need a CWB indexed corpus and word embeddings. Configure the
app via the [config file](app/instance/spheroscope.cfg).

## set-up ##
We use `pipenv`. install necessary modules via
#+BEGIN_SRC conf
./env-setup.sh
#+END_SRC

For running CQP queries (the default on the master branch), you will
have to install the CCC module separately.

## flask server ##
start the app like so:
#+BEGIN_SRC conf
./start-sterver.sh
#+END_SRC

## current modules ##
app/spheroscope/db.py
app/spheroscope/word_lists.py
app/spheroscope/queries.py
