resource "google_project_service" "compute_service" {
  project = var.account_id
  service = "compute.googleapis.com"
}

resource "google_project_service" "k8s_service" {
  project = var.account_id
  service = "container.googleapis.com"
}

resource "google_project_service" "usage_service" {
  project = var.account_id
  service = "serviceusage.googleapis.com"
}

// GVNIC VPC Isolated For Specific MRDMA Node Pools 
resource "google_compute_network" "gvnic_mrdma_vpc" {
  auto_create_subnetworks = false
  depends_on = [
    google_project_service.compute_service,
    google_project_service.usage_service,
    google_project_service.k8s_service
  ]
  mtu     = var.vpc_roce_mtu
  name    = "${var.machine_type}-${var.node_region}-${var.node_zone}-${var.reservation_affinity.reservations[0]}-gvnic"
  project = var.account_id

}

// GPUDirect - roce networks https://cloud.google.com/vpc/docs/rdma-network-profiles
// To see all available network profiles use "gcloud compute network-profiles list"
// Each of the zonal node pools gets its own vpc and subnet se
resource "google_compute_network" "vpc_gke_roce" {
  auto_create_subnetworks = false
  description             = "The vpc for the rnics attached to a3u and a4 vms."
  depends_on = [
    google_project_service.compute_service,
    google_project_service.usage_service,
    google_project_service.k8s_service
  ]
  mtu             = var.vpc_roce_mtu
  name            = "${var.machine_type}-${var.node_region}-${var.node_zone}-${var.reservation_affinity.reservations[0]}-mrdma"
  network_profile = "projects/${var.account_id}/global/networkProfiles/${var.node_region}-${var.node_zone}-vpc-roce"
  project         = var.account_id
}

// Each of the zonal node pools gets its own gke roce vpc and subnet set
resource "google_compute_subnetwork" "subnet_gke_roce" {
  for_each = {
    for item in flatten([
      for i in range(8) : [{
        index        = i
        machine_type = var.machine_type
        name         = var.node_pool_name
        node_region  = var.node_region
        unique_name  = "${var.machine_type}-${var.node_region}-${var.node_zone}-${var.reservation_affinity.reservations[0]}-${i}"
      }]
    ])
    : item.unique_name => item
  }

  description   = "The ${each.value.index % 8}th subnet for GPUDirect MRDMA network ${google_compute_network.vpc_gke_roce.name}"
  ip_cidr_range = format("192.169.%s.0/24", each.value.index)
  name          = "roce-sub-${each.value.unique_name}"
  network       = google_compute_network.vpc_gke_roce.id
  project       = var.account_id
  region        = each.value.node_region
}

// GVNIC - MRDMA workload subnets
// Used for a4 and a3u gvnic networks, each of the nodes needs to get it's own vpc for its gvnics
// and each of those has 1 subnet. Made wide for each of the zones to try and fit all required
// addrs in for multiple node pools in zone.
resource "google_compute_subnetwork" "subnet_gke_gvnic_mrdma" {
  description   = "Gvnic subnet for ${var.node_pool_name} in ${var.node_region}-${var.node_zone}"
  ip_cidr_range = "192.170.1.0/24"
  name          = "gvnic-sub-${var.machine_type}-${var.node_region}-${var.node_zone}-${var.reservation_affinity.reservations[0]}"
  network       = google_compute_network.gvnic_mrdma_vpc.id
  project       = var.account_id
  region        = var.node_region
}

resource "google_container_node_pool" "gpu_mrdma_node_pool" {
  cluster  = var.cluster_name
  location = var.node_region
  name     = "${var.node_pool_name}-${var.reservation_affinity.reservations[0]}"
  # The vpc and subnets are zone specific for mrdma so we need to define node pool per region & zones
  node_locations = ["${var.node_region}-${var.node_zone}"]
  project        = var.account_id
  provider       = google
  version        = var.min_gke_version

  autoscaling {
    total_min_node_count = var.autoscaling.total_min_node_count
    total_max_node_count = var.autoscaling.total_max_node_count
  }

  lifecycle {
    ignore_changes = [version]
  }

  management {
    auto_upgrade = false
  }


  network_config {
    dynamic "additional_node_network_configs" {
      for_each = concat(
        [
          {
            subnetwork = google_compute_subnetwork.subnet_gke_gvnic_mrdma.name
            network    = basename(google_compute_subnetwork.subnet_gke_gvnic_mrdma.network)
          }
        ],
        [
          for i in range(8) : {
            subnetwork = google_compute_subnetwork.subnet_gke_roce["${var.machine_type}-${var.node_region}-${var.node_zone}-${var.reservation_affinity.reservations[0]}-${i}"].name
            network    = basename(google_compute_subnetwork.subnet_gke_roce["${var.machine_type}-${var.node_region}-${var.node_zone}-${var.reservation_affinity.reservations[0]}-${i}"].network)
          }
        ]
      )
      content {
        subnetwork = additional_node_network_configs.value.subnetwork
        network    = additional_node_network_configs.value.network
      }
    }

    # This has to be set to "true", otherwise the cluster autoscaler won't be able to scale up a node group.
    enable_private_nodes = true
  }

  # Parameters used in creating the cluster's nodes.
  node_config {
    oauth_scopes = [
      "https://www.googleapis.com/auth/logging.write",
      "https://www.googleapis.com/auth/monitoring",
      "https://www.googleapis.com/auth/devstorage.read_only",
      "https://www.googleapis.com/auth/trace.append",
      "https://www.googleapis.com/auth/service.management.readonly",
      "https://www.googleapis.com/auth/servicecontrol",
    ]

    guest_accelerator {
      type  = var.gpu_accelerator.type
      count = var.gpu_accelerator.count
      gpu_driver_installation_config {
        gpu_driver_version = "LATEST"
      }
    }

    gvnic {
      enabled = true
    }

    fast_socket {
      enabled = false
    }

    labels = var.labels

    image_type      = var.image_type
    machine_type    = var.machine_type
    disk_size_gb    = var.disk_size
    disk_type       = var.disk_type
    preemptible     = false
    service_account = var.node_sa_email

    ephemeral_storage_local_ssd_config {
      local_ssd_count = var.ephemeral_storage_local_ssd_count
    }

    dynamic "reservation_affinity" {
      for_each = var.reservation_affinity != null ? [var.reservation_affinity] : []
      content {
        consume_reservation_type = reservation_affinity.value.type
        key                      = "compute.googleapis.com/reservation-name"

        values = reservation_affinity.value.reservations
      }
    }

    metadata = {
      # https://cloud.google.com/kubernetes-engine/docs/how-to/protecting-cluster-metadata
      disable-legacy-endpoints = "true"
    }

    tags = var.reservation_affinity.reservations
  }

  dynamic "placement_policy" {
    for_each = var.placement_policy != null ? [var.placement_policy] : []
    content {
      type         = placement_policy.value.type
      policy_name  = try(placement_policy.value.policy_name, null)
      tpu_topology = try(placement_policy.value.tpu_topology, null)
    }
  }

  timeouts {
    update = "60m"
  }
}
