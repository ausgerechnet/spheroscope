# spheroscope #

[![DOI](https://zenodo.org/badge/291022407.svg)](https://zenodo.org/badge/latestdoi/291022407)

**spheroscope** is a web app designated to argumentation mining. The backend is based on [cwb-ccc](https://pypi.org/project/cwb-ccc/), which runs multiply anchored CQP queries.

## Prerequisites ##
You will need a working installation of the [IMS Open Corpus Workbench (CWB)](http://cwb.sourceforge.net/), a CWB-indexed corpus, as well as word embeddings for most of what this app offers.  The python3 dependencies will be installed automatically if you follow the setup guide below.

## Setup ##

The recommended way is to use (pipenv)[https://pipenv.pypa.io/en/latest/]:

    python -m pip install pipenv
    pipenv install --dev

which creates a virtual environment and installs all required packages. The [Pipfile](Pipfile) is set to require Python3.9, you can change this e.g. via

    pipenv install --dev --python 3.8

Alternatively, you can use [setup.py](setup.py) or the [classic requirements file](requirements-classic.txt).


## Configuration ##
Configure the app via `cfg.py` in the app folder. You can find an [example config file](cfg_example.py) in the repository.

Set the `REGISTRY_PATH` to your CWB registry and `CACHE_PATH` to some directory where you have write access.

You can then

    make init
	
to populate your local instance with all queries, macros, and wordlists from the [library](library/).

You can now start the development flask server via

    make run

and navigate to [http://127.0.0.1:5000/](http://127.0.0.1:5000/) to access the interface.

## Corpus Settings ##
After starting the app, you will find [default corpus settings](instance/corpus_defaults.yaml) in your instance folder. You can change the defaults to your liking, taking into consideration the most common p- and s-attributes of your system corpora.

When selecting one of your corpora for the first time through the interface, a new folder and config file will be created for this corpus in your instance folder; the config file will be populated with the corpus defaults. Most settings, such as the `query` and `display` parameters, can be changed through the interface (http://127.0.0.1:5000/corpora/).

If you want to use similarity-based recommendations for wordlists, you should point the `embeddings` parameter to appropriate embeddings stored as `pymagnitude` files.

## License ##
The gold standard is licensed under a [Creative Commons Attribution-ShareAlike 4.0 International License (CC-BY-SA 4.0)](http://creativecommons.org/licenses/by-sa/4.0/).  ![http://creativecommons.org/licenses/by-sa/4.0/](https://i.creativecommons.org/l/by-sa/4.0/88x31.png)

The code and all other assets are licensed under the [GNU General Public License version 3 (GPL-3)](https://www.gnu.org/licenses/gpl-3.0.html).
