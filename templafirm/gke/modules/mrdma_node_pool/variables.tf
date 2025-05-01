variable "account_id" {
  type        = string
  description = "GCP Account id"
}

variable "autoscaling" {
  description = "Autoscaling policy"
  type = object({
    total_max_node_count = number
    total_min_node_count = number
  })
}

variable "cluster_name" {
  type        = string
  description = "name of cluster"
}

# Use this map to go from zones to subnet set idx for mrdma 
variable "count_zone_map" {
  type = map(string)
  default = {
    "us-central1-a" = 0
    "us-central1-b" = 1
  }
}

variable "disk_size" {
  description = "Size of disc"
  type        = number
}

variable "disk_type" {
  description = "Type of disc"
  type        = string
}

variable "ephemeral_storage_local_ssd_count" {
  default     = 0
  description = "SSD count to mount"
  type        = number
}

variable "gpu_accelerator" {
  description = "Accelerator to attach to machine"
  type = object({
    type  = string
    count = number
  })
}

variable "image_type" {
  description = "Type of image"
  type        = string
}

variable "labels" {
  default     = null
  description = "Node pool labels"
  type        = map(string)
}

variable "machine_type" {
  description = "Machine type for node pool"
  type        = string
}

variable "min_gke_version" {
  type        = string
  description = "Minimum gke version"
  default     = "1.30.5-gke.1699000"
}

variable "node_pool_name" {
  description = "Name of new node pool"
  type        = string
}

variable "node_region" {
  description = "Node region"
  type        = string
}

variable "node_sa_email" {
  description = "The email of service account assigned to node pool."
  type        = string
}

variable "node_zone" {
  description = "Node zone"
  type        = string
}

variable "placement_policy" {
  description = "Placement policy of node pool"
  type = object({
    type         = string
    policy_name  = optional(string)
    tpu_topology = optional(string)
  })
}

variable "reservation_affinity" {
  default     = null
  description = "Reservations for node pools"
  type = object({
    type         = string
    reservations = list(string)
  })
}

variable "vpc_roce_mtu" {
  type        = number
  description = "Maximum Transmission Unit in bytes for roce vpc."
  default     = 8896 // Setable between 1460 and 8896
  validation {
    condition = (
      var.vpc_roce_mtu >= 1460 &&
      var.vpc_roce_mtu <= 8896
    )
    error_message = "The MTU for roce value must be between 1460 and 8896 bytes."
  }
}

# Use map to go from count in roce vpcs to zones to create rdma vpc 
variable "zone_count_map" {
  type = map(string)
  default = {
    0 = "a"
    1 = "b"
  }
}
