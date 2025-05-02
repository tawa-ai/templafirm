import os
import tempfile
from typing import Any, Dict

import pytest

from templafirm.core.templater import Templater

from .test_provider import TEST_PROVIDER_META_PATH, BaseProviderTester


@pytest.fixture
def base_test_templater() -> Templater:
    Templater.register_provider("test_provider", BaseProviderTester(TEST_PROVIDER_META_PATH))
    templater = Templater()
    return templater


def test_templater_initialization(base_test_templater: Templater) -> None:
    assert "test_provider" in base_test_templater.list_providers()
    assert "gke" in base_test_templater.list_providers()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "expected_template_str, provider_name, template_inputs, templated_resource",
    [
        ("", "test_provider", {}, "test_empty_resource_template"),
        (
            'resource "test_resource" "test_resource_name" {\n  name                       = "test"\n}',
            "test_provider",
            {},
            "test_no_input_resource_template",
        ),
        (
            'resource "test_resource_input" "test_resource" {\n  input       = "test_input"\n}',
            "test_provider",
            {"resource_name": "test_resource", "input": "test_input"},
            "test_input_resource_template",
        ),
    ],
)
async def test_templater_generation(
    base_test_templater: Templater,
    expected_template_str: str,
    provider_name: str,
    template_inputs: Dict[str, Any],
    templated_resource: str,
) -> None:
    assert provider_name in base_test_templater.list_providers()

    provider_and_env = base_test_templater.return_provider(provider_key=provider_name)
    assert templated_resource in provider_and_env.provider._provider_meta_table.template_mapping.keys()

    base_test_templater.activate_provider("test_provider")
    templated_resource_rendered = await base_test_templater.render_template_resource(
        template_resource_inputs=template_inputs, template_resource_name=templated_resource
    )

    assert templated_resource_rendered == expected_template_str


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "expected_template_str, provider_name, template_inputs, templated_resource",
    [
        ("", "test_provider", {}, "test_empty_resource_template"),
        (
            'resource "test_resource" "test_resource_name" {\n  name                       = "test"\n}',
            "test_provider",
            {},
            "test_no_input_resource_template",
        ),
        (
            'resource "test_resource_input" "test_resource" {\n  input       = "test_input"\n}',
            "test_provider",
            {"resource_name": "test_resource", "input": "test_input"},
            "test_input_resource_template",
        ),
    ],
)
async def test_templater_generation_file(
    base_test_templater: Templater,
    expected_template_str: str,
    provider_name: str,
    template_inputs: Dict[str, Any],
    templated_resource: str,
) -> None:
    assert provider_name in base_test_templater.list_providers()

    provider_and_env = base_test_templater.return_provider(provider_key=provider_name)
    assert templated_resource in provider_and_env.provider._provider_meta_table.template_mapping.keys()

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_template.tf")
        base_test_templater.activate_provider("test_provider")
        await base_test_templater.render_template_resource_to_file(
            output_path=output_path, template_resource_inputs=template_inputs, template_resource_name=templated_resource
        )

        assert os.path.exists(output_path)

        with open(output_path, "r") as open_template_buffer:
            templated_resource = "".join(open_template_buffer.readlines())
        assert templated_resource == expected_template_str
