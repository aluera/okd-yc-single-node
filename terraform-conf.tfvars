dns_zone_name         = "example."
cluster_name          = "okd"
master_name           = "single-master"
master_cpu            = 4
master_ram            = 16
master_type_disk      = "network-hdd"
size_disk_master_node = "120"
network_name          = "okd_network"
image_id              = "fd865udut6b1gvgh5igh"
platform_id           = "standard-v3"
scheduling_policy     = true
subnets = {
  zone           = "ru-central1-a"
  v4_cidr_blocks = "10.88.1.0/24"
}
labels = {
  tag        = "okd",
  demo       = "false",
  created_by = "okd-yc-upi"
}
