#!/usr/bin/python3
import time

dns_zone_name = "example."
cluster_name = "okd"
master_name = "single-master"
bucket_name = f"bucket-bootstrap-{cluster_name}-{int(time.time())}"
master_cpu = 4
master_ram = 16
master_type_disk = "network-hdd"
size_disk_master_node = "120"
network_name = "okd_network"
image_id = "fd8u9lgdcukfl03sik2n"
platform_id = "standard-v3"
scheduling_policy = "true"
zone = "ru-central1-a"
v4_cidr_blocks = "10.88.1.0/24"
pullSecret = '{"auths":{"fake":{"auth": "bar"}}}'
