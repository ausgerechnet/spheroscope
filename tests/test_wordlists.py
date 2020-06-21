from spheroscope.wordlists import get_frequencies
from spheroscope import spheroscope

import os
import pytest
import tempfile


@pytest.fixture
def client():

    db_fd, spheroscope.app.config['DATABASE'] = tempfile.mkstemp()
    spheroscope.app.config['TESTING'] = True

    with spheroscope.app.test_client() as client:
        with spheroscope.app.app_context():
            spheroscope.init_db()
        yield client

    os.close(db_fd)
    os.unlink(spheroscope.app.config['DATABASE'])


def login(client, username, password):
    return client.post('/login', data=dict(
        username=username,
        password=password
    ), follow_redirects=True)


def logout(client):
    return client.get('/logout', follow_redirects=True)


@pytest.mark.now
def test_empty_db(client):
    """Start with a blank database."""

    rv = client.get('/')
    assert b'No entries here so far' in rv.data


def test_show_frequencies(client):
    words = ['test', 'angela']
    p_att = 'lemma'
    test = get_frequencies(words, p_att)
    print(test)
