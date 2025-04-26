import pytest

from templafirm.core.meta_table import ResourceTemplate
from templafirm.gke.gke_provider import GKEProvider

EXPECTED_PROVIDER_VERSION = "0.0.1"
EXPECTED_PROVIDER_NAME = "gke"


@pytest.fixture
def gke_test_provider() -> GKEProvider:
    return GKEProvider()


def test_gke_provider_initialization(gke_test_provider: GKEProvider) -> None:
    assert gke_test_provider.version == EXPECTED_PROVIDER_VERSION
    assert gke_test_provider.name == EXPECTED_PROVIDER_NAME


def test_gke_provider_mrdma_node_pool_resource(gke_test_provider: GKEProvider) -> None:
    expected_mrdma_node_pool_resource = ResourceTemplate(
        name="mrdma_node_pool", version="0.0.1", template_file_path="gke_mrdma_node_pool.jinja2", template_inputs=[]
    )
    assert expected_mrdma_node_pool_resource == gke_test_provider["mrdma_node_pool"]
