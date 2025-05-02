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
        name="mrdma_node_pool",
        version="0.0.1",
        template_file_path="node_pools/mrdma_node_pool.jinja2",
        template_inputs={
            "cluster_name",
            "disk_size",
            "dist_type",
            "ephemeral_storage_local_ssd_count",
            "gcp_project_id",
            "gpu_accelerator_count",
            "gpu_accelerator_type",
            "image_type",
            "labels",
            "machine_type",
            "node_pool_name",
            "node_region",
            "node_sa_email",
            "node_zone",
            "placement_policy_type",
            "reservation_ids",
            "reservation_type",
            "total_max_node_count",
            "total_min_node_count",
        },
    )
    assert expected_mrdma_node_pool_resource == gke_test_provider["mrdma_node_pool"]
