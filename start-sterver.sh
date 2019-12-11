#! /bin/sh

cd app || exit
export FLASK_APP=spheroscope
export FLASK_ENV=development
flask init-db
flask run
