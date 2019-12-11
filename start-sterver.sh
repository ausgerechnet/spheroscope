#! /bin/sh

cd app || exit
export FLASK_APP=spheroscope
export FLASK_ENV=development
flask init-db
python3 instance/import-wordlists.py
python3 instance/import-queries.py
flask run
