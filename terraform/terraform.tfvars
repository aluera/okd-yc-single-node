dns_zone_name         = "internal."
cluster_name          = "okd"
master_name           = "single-master"
master_cpu            = 4
master_ram            = 16
master_type_disk      = "network-hdd"
size_disk_master_node = "120"
network_name          = "okd_network"
image_id              = "fd8u9lgdcukfl03sik2n"
platform_id           = "standard-v3"
scheduling_policy     = true
labels = {
  tag        = "okd",
  demo       = "false",
  created_by = "okd-yc-upi"
}
subnets = {
  zone           = "ru-central1-a"
  v4_cidr_blocks = "10.88.1.0/24"
}
#{'retry_count': 0, 'max_retry_count': 3}