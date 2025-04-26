import tempfile

import pytest

from templafirm.core.templater import Templater

from .test_provider import TEST_PROVIDER_META_PATH, BaseProviderTester


@pytest.fixture
def base_test_templater() -> Templater:
    with tempfile.TemporaryDirectory() as tmpdir:
        Templater.register_provider("test_provider", BaseProviderTester(TEST_PROVIDER_META_PATH))
        templater = Templater(template_directory=tmpdir)
        return templater


def test_templater_initialization(base_test_templater: Templater) -> None:
    assert "test_provider" in base_test_templater.list_providers()
    assert "eai" in base_test_templater.list_providers()
