import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
import tftest

from templafirm.core.templater import Templater


@pytest_asyncio.fixture
async def plan() -> AsyncGenerator[tftest.TerraformPlanOutput]:
    # purposefully do not use a temp dir as it borks tf import paths
    templater = Templater()

    template_resource_name = "mrdma_node_pool"
    template_inputs = {
        "cluster_name": "test_cluster",
        "disk_size": "100",
        "dist_type": "fast",
        "ephemeral_storage_local_ssd_count": "0",
        "gcp_project_id": "test-project",
        "gpu_accelerator_count": "1",
        "gpu_accelerator_type": "h200",
        "image_type": "image_type",
        "labels": '{"label": "label"}',
        "machine_type": "a3-ultragpu-8g",
        "node_pool_name": "test-node-pool",
        "node_region": "us-central1",
        "node_sa_email": "somebody@email.com",
        "node_zone": "b",
        "placement_policy_type": "COMPACT",
        "reservation_ids": '["test-id"]',
        "reservation_type": "SPECIFIC_RESERVATION",
        "total_max_node_count": "4",
        "total_min_node_count": "0",
    }

    node_pool_dir = os.path.join(templater.return_provider("gke").provider.template_directory_path(), "node_pools")
    output_path = os.path.join(node_pool_dir, "test_template.tf")
    templater.activate_provider("gke")
    await templater.render_template_resource_to_file(
        output_path=output_path, template_resource_inputs=template_inputs, template_resource_name=template_resource_name
    )

    assert os.path.exists(output_path)

    tf_tester = tftest.TerraformTest(node_pool_dir, enable_cache=True)
    tf_tester.setup()
    tf_tester.init(input=True)
    yield tf_tester.plan(output=True)
    os.remove(output_path)


@pytest.mark.asyncio
async def test_mrdma(plan: tftest.TerraformPlanOutput) -> None:
    expected_subnet_set = {
        "module.mrmda_node_pool.google_compute_network.vpc_gke_roce",
        'module.mrmda_node_pool.google_compute_subnetwork.subnet_gke_roce["a3-ultragpu-8g-us-central1-b-test-id-0"]',
        'module.mrmda_node_pool.google_compute_subnetwork.subnet_gke_roce["a3-ultragpu-8g-us-central1-b-test-id-1"]',
        'module.mrmda_node_pool.google_compute_subnetwork.subnet_gke_roce["a3-ultragpu-8g-us-central1-b-test-id-2"]',
        'module.mrmda_node_pool.google_compute_subnetwork.subnet_gke_roce["a3-ultragpu-8g-us-central1-b-test-id-3"]',
        'module.mrmda_node_pool.google_compute_subnetwork.subnet_gke_roce["a3-ultragpu-8g-us-central1-b-test-id-4"]',
        'module.mrmda_node_pool.google_compute_subnetwork.subnet_gke_roce["a3-ultragpu-8g-us-central1-b-test-id-5"]',
        'module.mrmda_node_pool.google_compute_subnetwork.subnet_gke_roce["a3-ultragpu-8g-us-central1-b-test-id-6"]',
        'module.mrmda_node_pool.google_compute_subnetwork.subnet_gke_roce["a3-ultragpu-8g-us-central1-b-test-id-7"]',
    }
    resource_change_key_set = set(plan.resource_changes.keys())
    assert expected_subnet_set.intersection(resource_change_key_set) == expected_subnet_set

    # test the name of the gke_roce net
    mrdma_roce_change = plan.resource_changes["module.mrmda_node_pool.google_compute_network.vpc_gke_roce"]
    assert mrdma_roce_change["change"]["after"]["name"] == "a3-ultragpu-8g-us-central1-b-test-id-mrdma"

    # test data elements
    for i in range(0, 8):
        mrdma_subnet_change = plan.resource_changes[
            f'module.mrmda_node_pool.google_compute_subnetwork.subnet_gke_roce["a3-ultragpu-8g-us-central1-b-test-id-{i}"]'
        ]["change"]["after"]
        assert (
            mrdma_subnet_change["description"]
            == f"The {i}th subnet for GPUDirect MRDMA network a3-ultragpu-8g-us-central1-b-test-id-mrdma"
        )
        assert mrdma_subnet_change["ip_cidr_range"] == f"192.169.{i}.0/24"
        assert mrdma_subnet_change["name"] == f"roce-sub-a3-ultragpu-8g-us-central1-b-test-id-{i}"
        assert mrdma_subnet_change["project"] == "test-project"
        assert mrdma_subnet_change["region"] == "us-central1"


@pytest.mark.asyncio
async def test_gvnic(plan: tftest.TerraformPlanOutput) -> None:
    expected_net_set = {
        "module.mrmda_node_pool.google_compute_network.gvnic_mrdma_vpc",
        "module.mrmda_node_pool.google_compute_subnetwork.subnet_gke_gvnic_mrdma",
    }
    resource_change_key_set = set(plan.resource_changes.keys())
    assert expected_net_set.intersection(resource_change_key_set) == expected_net_set

    gvnic_net_change = plan.resource_changes["module.mrmda_node_pool.google_compute_network.gvnic_mrdma_vpc"]
    assert gvnic_net_change["change"]["after"]["name"] == "a3-ultragpu-8g-us-central1-b-test-id-gvnic"

    gvnic_subnet_change = plan.resource_changes[
        "module.mrmda_node_pool.google_compute_subnetwork.subnet_gke_gvnic_mrdma"
    ]["change"]["after"]
    assert gvnic_subnet_change["ip_cidr_range"] == "192.170.1.0/24"
    assert gvnic_subnet_change["name"] == "gvnic-sub-a3-ultragpu-8g-us-central1-b-test-id"
    assert gvnic_subnet_change["project"] == "test-project"
    assert gvnic_subnet_change["region"] == "us-central1"
