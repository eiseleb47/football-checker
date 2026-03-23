import pytest
import app as app_module


@pytest.fixture
def client():
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as c:
        yield c


@pytest.fixture(autouse=True)
def clear_cache():
    """Wipe the in-memory cache before and after every test."""
    app_module._cache.clear()
    yield
    app_module._cache.clear()
