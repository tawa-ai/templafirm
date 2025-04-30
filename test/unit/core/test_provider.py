import os
import pathlib
from typing import Any, Dict

import pytest
import yaml

from templafirm.core.meta_table import ProviderMetaTable, ResourceTemplate
from templafirm.core.provider import Provider
from test import assets

TEST_PROVIDER_META_PATH = "test/assets/test_provider_meta.yaml"


class BaseProviderTester(Provider):
    def __init__(self, provider_meta_path: str):
        super().__init__(provider_meta_path)

    def template_directory_path(self) -> str:
        template_module_file_path = pathlib.Path(os.path.abspath(assets.__file__))
        template_module_file_path = pathlib.Path(os.path.join(os.getcwd(), template_module_file_path))
        return str(template_module_file_path.parent)


@pytest.fixture
def base_test_provider() -> BaseProviderTester:
    return BaseProviderTester(TEST_PROVIDER_META_PATH)


@pytest.fixture
def base_test_provider_raw_yaml() -> Dict[str, Any]:
    with open(TEST_PROVIDER_META_PATH, "r") as open_meta_yaml_buffer:
        yaml_data = yaml.safe_load(open_meta_yaml_buffer)
        return yaml_data


def test_base_provider_initialization(
    base_test_provider: Provider, base_test_provider_raw_yaml: Dict[str, Any]
) -> None:
    expected_template_object = ProviderMetaTable(
        name=base_test_provider_raw_yaml["name"],
        version=base_test_provider_raw_yaml["version"],
        template_mapping={
            "test_empty_resource_template": ResourceTemplate(
                name=base_test_provider_raw_yaml["template_mapping"]["test_empty_resource_template"]["name"],
                version=base_test_provider_raw_yaml["template_mapping"]["test_empty_resource_template"]["version"],
                template_file_path=base_test_provider_raw_yaml["template_mapping"]["test_empty_resource_template"][
                    "template_file_path"
                ],
            ),
            "test_no_input_resource_template": ResourceTemplate(
                name=base_test_provider_raw_yaml["template_mapping"]["test_no_input_resource_template"]["name"],
                version=base_test_provider_raw_yaml["template_mapping"]["test_no_input_resource_template"]["version"],
                template_file_path=base_test_provider_raw_yaml["template_mapping"]["test_no_input_resource_template"][
                    "template_file_path"
                ],
            ),
            "test_input_resource_template": ResourceTemplate(
                name=base_test_provider_raw_yaml["template_mapping"]["test_input_resource_template"]["name"],
                version=base_test_provider_raw_yaml["template_mapping"]["test_input_resource_template"]["version"],
                template_file_path=base_test_provider_raw_yaml["template_mapping"]["test_input_resource_template"][
                    "template_file_path"
                ],
            ),
        },
    )
    assert base_test_provider._provider_meta_table == expected_template_object


def test_base_provider_resources(base_test_provider: Provider, base_test_provider_raw_yaml: Dict[str, Any]) -> None:
    expected_resource_keys = base_test_provider_raw_yaml["template_mapping"].keys()
    assert base_test_provider.resources == expected_resource_keys


def test_base_provider_version(base_test_provider: Provider, base_test_provider_raw_yaml: Dict[str, Any]) -> None:
    assert base_test_provider.version == base_test_provider_raw_yaml["version"]


def test_base_provider_resource_get(base_test_provider: Provider, base_test_provider_raw_yaml: Dict[str, Any]) -> None:
    expected_resource = ResourceTemplate(
        name=base_test_provider_raw_yaml["template_mapping"]["test_empty_resource_template"]["name"],
        version=base_test_provider_raw_yaml["template_mapping"]["test_empty_resource_template"]["version"],
        template_file_path=base_test_provider_raw_yaml["template_mapping"]["test_empty_resource_template"][
            "template_file_path"
        ],
    )
    assert base_test_provider["test_empty_resource_template"] == expected_resource
