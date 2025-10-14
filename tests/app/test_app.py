from streamlit.testing.v1 import AppTest

from app import app, repositories


class FakeRepository(repositories.AbstractRepository): ...


def test_app():
    app_test = AppTest.from_function(app.main, args=(FakeRepository(),))
    app_test.run()
    assert not app_test.exception
