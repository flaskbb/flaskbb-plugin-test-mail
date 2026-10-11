import pytest
from flask import g
from flask_login.test_client import FlaskLoginClient
from tests.fixtures.app import *
from tests.fixtures.forum import *
from tests.fixtures.user import *


@pytest.fixture(scope="package")
def tested_plugins():
    return ["test mail"]


@pytest.fixture
def client(application, default_settings, default_groups, monkeypatch):
    # FlaskLoginClient doesn't store the session identifier, so "basic"
    # session protection would mark every login as stale on the first request
    monkeypatch.setattr(application.login_manager, "session_protection", None)
    monkeypatch.setattr(application, "test_client_class", FlaskLoginClient)

    def make(user=None):
        # requests reuse the package-wide app context, so flask-login's cached
        # g._login_user would otherwise leak between clients and tests
        g.pop("_login_user", None)
        return application.test_client(user=user)

    yield make
    g.pop("_login_user", None)


@pytest.fixture
def no_csrf(application, monkeypatch):
    monkeypatch.setitem(application.config, "WTF_CSRF_ENABLED", False)


@pytest.fixture
def sent_mails(monkeypatch):
    mails = []
    monkeypatch.setattr("test_mail.tasks.send_email", lambda **kwargs: mails.append(kwargs))
    return mails
