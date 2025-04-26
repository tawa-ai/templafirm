import pytest

from templafirm.core.meta_table import ResourceTemplate
from templafirm.eai.eai_provider import EAIProvider

EXPECTED_PROVIDER_VERSION = "0.0.1"
EXPECTED_PROVIDER_NAME = "eai"


@pytest.fixture
def eai_test_provider() -> EAIProvider:
    return EAIProvider()


def test_eai_provider_initialization(eai_test_provider: EAIProvider) -> None:
    assert eai_test_provider.version == EXPECTED_PROVIDER_VERSION
    assert eai_test_provider.name == EXPECTED_PROVIDER_NAME


def test_eai_provider_mrdma_node_pool_resource(eai_test_provider: EAIProvider) -> None:
    expected_mrdma_node_pool_resource = ResourceTemplate(
        name="mrdma_node_pool", version="0.0.1", template_file_path="eai_mrdma_node_pool.jinja2", template_inputs=[]
    )
    assert expected_mrdma_node_pool_resource == eai_test_provider["mrdma_node_pool"]
