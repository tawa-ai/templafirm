import os
import tempfile
from typing import Any, Dict

import pytest

from templafirm.core.templater import Templater


@pytest.fixture
def gke_test_templater() -> Templater:
    templater = Templater()
    return templater


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "expected_template_str, template_inputs, templated_resource",
    [
        (
            'module "mrmda_node_pool" {\n  source = "../../modules/mrdma_node_pool/"\n\n  account_id                        = "test-project"\n  autoscaling                       = {\n    total_min_node_count = "0"\n    total_max_node_count = "4"\n  }\n  cluster_name                      = "test_cluster"\n  disk_size                         = "100"\n  disk_type                         = "fast"\n  ephemeral_storage_local_ssd_count = "0"\n  gpu_accelerator                   = {\n    count = "1"\n    type  = "h200"\n  }\n  image_type                        = "image_type"\n  labels                            = {\'label\': \'label\'}\n  machine_type                      = "a3-ultragpu-8g"\n  node_pool_name                    = "test-node-pool" \n  node_region                       = "us-central1"\n  node_sa_email                     = "somebody@email.com" \n  node_zone                         = "b"\n  placement_policy                  = {\n    type = "COMPACT"\n  }\n  reservation_affinity              = {\n    type = "SPECIFIC_RESERVATION"\n    reservations = ["test_id"]\n  }\n}',
            {
                "cluster_name": "test_cluster",
                "disk_size": "100",
                "dist_type": "fast",
                "ephemeral_storage_local_ssd_count": "0",
                "gcp_project_id": "test-project",
                "gpu_accelerator_count": "1",
                "gpu_accelerator_type": "h200",
                "image_type": "image_type",
                "labels": {"label": "label"},
                "machine_type": "a3-ultragpu-8g",
                "node_pool_name": "test-node-pool",
                "node_region": "us-central1",
                "node_sa_email": "somebody@email.com",
                "node_zone": "b",
                "placement_policy_type": "COMPACT",
                "reservation_ids": '["test_id"]',
                "reservation_type": "SPECIFIC_RESERVATION",
                "total_max_node_count": "4",
                "total_min_node_count": "0",
            },
            "mrdma_node_pool",
        ),
    ],
)
async def test_gke_templater_generation(
    gke_test_templater: Templater,
    expected_template_str: str,
    template_inputs: Dict[str, Any],
    templated_resource: str,
) -> None:
    provider_and_env = gke_test_templater.return_provider(provider_key="gke")
    assert templated_resource in provider_and_env.provider._provider_meta_table.template_mapping.keys()

    gke_test_templater.activate_provider("gke")
    templated_resource_rendered = await gke_test_templater.render_template_resource(
        template_resource_inputs=template_inputs, template_resource_name=templated_resource
    )
    assert templated_resource_rendered == expected_template_str


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "expected_template_str, template_inputs, templated_resource",
    [
        (
            'module "mrmda_node_pool" {\n  source = "../../modules/mrdma_node_pool/"\n\n  account_id                        = "test-project"\n  autoscaling                       = {\n    total_min_node_count = "0"\n    total_max_node_count = "4"\n  }\n  cluster_name                      = "test_cluster"\n  disk_size                         = "100"\n  disk_type                         = "fast"\n  ephemeral_storage_local_ssd_count = "0"\n  gpu_accelerator                   = {\n    count = "1"\n    type  = "h200"\n  }\n  image_type                        = "image_type"\n  labels                            = {\'label\': \'label\'}\n  machine_type                      = "a3-ultragpu-8g"\n  node_pool_name                    = "test-node-pool" \n  node_region                       = "us-central1"\n  node_sa_email                     = "somebody@email.com" \n  node_zone                         = "b"\n  placement_policy                  = {\n    type = "COMPACT"\n  }\n  reservation_affinity              = {\n    type = "SPECIFIC_RESERVATION"\n    reservations = ["test_id"]\n  }\n}',
            {
                "cluster_name": "test_cluster",
                "disk_size": "100",
                "dist_type": "fast",
                "ephemeral_storage_local_ssd_count": "0",
                "gcp_project_id": "test-project",
                "gpu_accelerator_count": "1",
                "gpu_accelerator_type": "h200",
                "image_type": "image_type",
                "labels": {"label": "label"},
                "machine_type": "a3-ultragpu-8g",
                "node_pool_name": "test-node-pool",
                "node_region": "us-central1",
                "node_sa_email": "somebody@email.com",
                "node_zone": "b",
                "placement_policy_type": "COMPACT",
                "reservation_ids": '["test_id"]',
                "reservation_type": "SPECIFIC_RESERVATION",
                "total_max_node_count": "4",
                "total_min_node_count": "0",
            },
            "mrdma_node_pool",
        ),
    ],
)
async def test_gke_templater_file_generation(
    gke_test_templater: Templater,
    expected_template_str: str,
    template_inputs: Dict[str, Any],
    templated_resource: str,
) -> None:
    provider_and_env = gke_test_templater.return_provider(provider_key="gke")
    assert templated_resource in provider_and_env.provider._provider_meta_table.template_mapping.keys()

    gke_test_templater.activate_provider("gke")

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_template.tf")
        gke_test_templater.activate_provider("gke")
        await gke_test_templater.render_template_resource_to_file(
            output_path=output_path, template_resource_inputs=template_inputs, template_resource_name=templated_resource
        )

        assert os.path.exists(output_path)

        with open(output_path, "r") as open_template_buffer:
            templated_resource = "".join(open_template_buffer.readlines())
        assert templated_resource == expected_template_str
