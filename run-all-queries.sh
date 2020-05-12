#!/bin/sh

export FLASK_APP=spheroscope
export FLASK_ENV=development
flask init-db
flask import-lib
flask run-all-queries
