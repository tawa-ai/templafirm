import tempfile
from typing import Any, Dict

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
    assert "gke" in base_test_templater.list_providers()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "provider_name, templated_resource, template_inputs, expected_template_str",
    [
        ("test_provider", "test_empty_resource_template", {}, ""),
        (
            "test_provider",
            "test_no_input_resource_template",
            {},
            'resource "test_resource" "test_resource_name" {\n  name                       = "test"\n}',
        ),
        (
            "test_provider",
            "test_input_resource_template",
            {"resource_name": "test_resource", "input": "test_input"},
            'resource "test_resource_input" "test_resource" {\n  input       = "test_input"\n}',
        ),
    ],
)
async def test_templater_generation(
    base_test_templater: Templater,
    provider_name: str,
    templated_resource: str,
    template_inputs: Dict[str, Any],
    expected_template_str: str,
) -> None:
    assert provider_name in base_test_templater.list_providers()

    provider_and_env = base_test_templater.return_provider(provider_key=provider_name)
    assert templated_resource in provider_and_env.provider._provider_meta_table.template_mapping.keys()

    base_test_templater.activate_provider("test_provider")
    templated_resource = await base_test_templater.render_template_resource(templated_resource, template_inputs)

    assert templated_resource == expected_template_str
