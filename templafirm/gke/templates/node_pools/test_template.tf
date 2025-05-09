module "mrdma_node_pool_test" {
  source = "../../modules/mrdma_node_pool/"

  account_id                        = "test-project"
  autoscaling                       = {
    total_min_node_count = "0"
    total_max_node_count = "4"
  }
  cluster_name                      = "test_cluster"
  disk_size                         = "100"
  disk_type                         = "fast"
  ephemeral_storage_local_ssd_count = "0"
  gpu_accelerator                   = {
    count = "1"
    type  = "h200"
  }
  image_type                        = "image_type"
  labels                            = {"label": "label"}
  machine_type                      = "a3-ultragpu-8g"
  node_pool_name                    = "test-node-pool" 
  node_region                       = "us-central1"
  node_sa_email                     = "somebody@email.com" 
  node_zone                         = "b"
  placement_policy                  = {
    type = "COMPACT"
  }
  reservation_affinity              = {
    type = "SPECIFIC_RESERVATION"
    reservations = ["test-id"]
  }
}