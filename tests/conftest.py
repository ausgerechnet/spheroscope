import os
import tempfile

import pytest

from spheroscope import create_app
from spheroscope.database import init_db, import_library


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # create a temporary file to isolate the database for each test
    db_fd, db_path = tempfile.mkstemp()
    # create the app with common test config
    app = create_app({
        "TESTING": True,
        "DATABASE": db_path,
        "DB_NAME": "test.sqlite",
        "DB_USERNAME": "admin",
        "DB_PASSWORD": "0000",
        "SECRET_KEY": "testing",
        "REGISTRY_PATH": "/home/ausgerechnet/corpora/cwb/registry/",
        "CACHE_PATH": "/tmp/spheroscope-cache/"
    })

    # create the database and load test data
    with app.app_context():
        init_db()
        import_library()
    yield app

    # close and remove the temporary database
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()


class AuthActions(object):

    def __init__(self, client):
        self._client = client

    def login(self, username="admin", password="0000"):
        return self._client.post(
            "/auth/login", data={"username": username, "password": password}
        )

    def logout(self):
        return self._client.get("/auth/logout")


@pytest.fixture
def auth(client):

    return AuthActions(client)
