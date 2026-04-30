import pytest

from tests.fake_infer_server import start_fake_infer_server


@pytest.fixture
def infer_url():
    url, shutdown = start_fake_infer_server()
    try:
        yield url
    finally:
        shutdown()
