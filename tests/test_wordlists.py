from spheroscope.wordlists import read_from_path, read_from_db
from spheroscope.wordlists import write, delete
from spheroscope.wordlists import lib2db

import pytest


def test_read_from_path():
    path = (
        "/home/ausgerechnet/repositories/spheroscope/library/"
        "BREXIT_V20190522_DEDUP/wordlists/adj_adv_difference.txt"
    )
    wordlist = read_from_path(path)
    print(wordlist)


def test_write(app):

    user_id = 1
    path = (
        "/home/ausgerechnet/repositories/spheroscope/library/"
        "BREXIT_V20190522_DEDUP/wordlists/adj_adv_difference.txt"
    )
    wordlist = read_from_path(path)
    wordlist['user_id'] = user_id
    with app.app_context():
        write(wordlist)


def test_read_from_db_all(app):

    user_id = 1
    path = (
        "/home/ausgerechnet/repositories/spheroscope/library/"
        "BREXIT_V20190522_DEDUP/wordlists/adj_adv_difference.txt"
    )
    wordlist = read_from_path(path)
    wordlist['user_id'] = user_id
    with app.app_context():
        write(wordlist)
        wordlists = read_from_db()
    print(wordlists)


def test_read_from_db_one(app):

    user_id = 1
    path = (
        "/home/ausgerechnet/repositories/spheroscope/library/"
        "BREXIT_V20190522_DEDUP/wordlists/adj_adv_difference.txt"
    )
    wordlist = read_from_path(path)
    wordlist['user_id'] = user_id
    with app.app_context():
        write(wordlist)
        wordlists = read_from_db([1])
    print(wordlists)


def test_delete(app):

    user_id = 1
    path = (
        "/home/ausgerechnet/repositories/spheroscope/library/"
        "BREXIT_V20190522_DEDUP/wordlists/adj_adv_difference.txt"
    )
    wordlist = read_from_path(path)
    wordlist['user_id'] = user_id
    with app.app_context():
        write(wordlist)
        delete(1)


@pytest.mark.now
def test_lib2db(app):
    with app.app_context():
        lib2db()
        wordlists = read_from_db()
    print(wordlists)
