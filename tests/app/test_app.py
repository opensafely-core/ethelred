import contextlib
import datetime

import pandas
from streamlit.testing.v1 import AppTest

from app import app, repositories


# I'm not sure if _get_user_info is the best thing to mock, so this is a placeholder
@contextlib.contextmanager
def patch_user_info(is_logged_in):
    from unittest.mock import patch

    import streamlit.user_info

    def mock__get_user_info():
        return {"is_logged_in": is_logged_in, "email": "user@example.com"}

    with patch.object(streamlit.user_info, "_get_user_info", new=mock__get_user_info):
        yield


class FakeRepository(repositories.AbstractRepository):
    def get_earliest_login_date(self):
        return datetime.date(2025, 1, 1)

    def get_latest_login_date(self):
        return datetime.date(2025, 1, 1)

    def get_logins_per_day(self, from_, to_):
        return pandas.DataFrame({"date": [datetime.date(2025, 1, 1)], "count": [1]})


def test_app():
    app_test = AppTest.from_function(app._main, args=(FakeRepository(),))
    app_test.run()
    assert not app_test.exception

    assert app_test.title[0].value == "Ethelred"


def test_logged_in(monkeypatch):
    monkeypatch.setenv("AUTH_REDIRECT_URI", "test-redirect-uri")
    monkeypatch.setenv("AUTH_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("AUTH_CLIENT_SECRET", "test-client-secret")
    monkeypatch.setenv("AUTH_COOKIE_SECRET", "test-cookie-secret")
    monkeypatch.setenv(
        "AUTH_SERVER_METADATA_URL",
        "https://accounts.google.com/.well-known/openid-configuration",
    )

    def _main():
        import streamlit

        streamlit.title("You are logged in")

    with patch_user_info(is_logged_in=True):
        app_test = AppTest.from_function(app.main, args=(_main,))
        app_test.run()

        assert not app_test.exception
        assert app_test.title[0].value == "You are logged in"


def test_not_logged_in(monkeypatch):
    monkeypatch.setenv("AUTH_REDIRECT_URI", "test-redirect-uri")
    monkeypatch.setenv("AUTH_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("AUTH_CLIENT_SECRET", "test-client-secret")
    monkeypatch.setenv("AUTH_COOKIE_SECRET", "test-cookie-secret")
    monkeypatch.setenv(
        "AUTH_SERVER_METADATA_URL",
        "https://accounts.google.com/.well-known/openid-configuration",
    )

    def _main():
        import streamlit

        streamlit.title("You should not see this")

    # By default, AppTest's state is that the user is not logged in.
    # But we can use `patch_user_info` here if we want to too.
    app_test = AppTest.from_function(app.main, args=(_main,))
    app_test.run()

    assert not app_test.exception
    assert app_test.title[0].value == "Please log in"
