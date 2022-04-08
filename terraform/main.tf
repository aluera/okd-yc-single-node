provider "yandex" {
  service_account_key_file = "../key.json"
  folder_id                = ""
}

locals {
  folder_id = data.yandex_iam_service_account.client.folder_id
}

data "yandex_iam_service_account" "client" {
  service_account_id = ""
}

resource "yandex_vpc_network" "this" {
  description = var.network_description
  name        = var.network_name
  labels      = var.labels
  folder_id   = local.folder_id
}

resource "yandex_vpc_subnet" "this" {
  name           = var.subnets.zone
  description    = "${var.network_name} subnet for zone ${var.subnets.zone}"
  v4_cidr_blocks = [var.subnets.v4_cidr_blocks]
  zone           = var.subnets.zone
  network_id     = yandex_vpc_network.this.id
  folder_id      = local.folder_id
  dhcp_options {
    domain_name = var.dns_zone_name
  }
  labels = var.labels
}

# DNS 
resource "yandex_dns_zone" "subnet_dns_zone" {
  name             = "${var.subnets.zone}-okd-zone"
  labels           = var.labels
  zone             = var.dns_zone_name
  public           = false
  private_networks = [yandex_vpc_network.this.id]
}

resource "yandex_dns_recordset" "apps-int" {
  zone_id = yandex_dns_zone.subnet_dns_zone.id
  name    = "*.apps.${var.cluster_name}"
  type    = "A"
  ttl     = 200
  data    = [yandex_compute_instance.master.network_interface[0].ip_address]
}

resource "yandex_dns_recordset" "api" {
  zone_id = yandex_dns_zone.subnet_dns_zone.id
  name    = "api.${var.cluster_name}"
  type    = "A"
  ttl     = 200
  data    = [yandex_compute_instance.master.network_interface[0].ip_address, yandex_compute_instance.bootstrap.network_interface[0].ip_address]
}

resource "yandex_dns_recordset" "api-int" {
  zone_id = yandex_dns_zone.subnet_dns_zone.id
  name    = "api-int.${var.cluster_name}"
  type    = "A"
  ttl     = 200
  data    = [yandex_compute_instance.master.network_interface[0].ip_address, yandex_compute_instance.bootstrap.network_interface[0].ip_address]
}
resource "yandex_dns_recordset" "bootstrap-dns" {
  zone_id = yandex_dns_zone.subnet_dns_zone.id
  name    = "bootstrap.${var.cluster_name}"
  type    = "A"
  ttl     = 200
  data    = [yandex_compute_instance.bootstrap.network_interface[0].ip_address]
}
resource "yandex_dns_recordset" "master-dns" {
  zone_id = yandex_dns_zone.subnet_dns_zone.id
  name    = "${var.master_name}.${var.cluster_name}"
  type    = "A"
  ttl     = 200
  data    = [yandex_compute_instance.master.network_interface[0].ip_address]
}



resource "yandex_iam_service_account_static_access_key" "sa-static-key" {
  service_account_id = data.yandex_iam_service_account.client.id
  description        = "static access key for object storage"
}

resource "yandex_storage_bucket" "ignition" {
  bucket        = "bootstrap-ignition-${var.cluster_name}"
  force_destroy = true
  grant {
    type        = "Group"
    permissions = ["READ"]
    uri         = "http://acs.amazonaws.com/groups/global/AllUsers"
  }
  access_key = yandex_iam_service_account_static_access_key.sa-static-key.access_key
  secret_key = yandex_iam_service_account_static_access_key.sa-static-key.secret_key
  depends_on = [
    data.yandex_iam_service_account.client
  ]
}

resource "yandex_storage_object" "okd-ignition" {
  bucket     = yandex_storage_bucket.ignition.id
  key        = "bootstrap.ign"
  source     = "../okd-ignition/bootstrap.ign"
  access_key = yandex_iam_service_account_static_access_key.sa-static-key.access_key
  secret_key = yandex_iam_service_account_static_access_key.sa-static-key.secret_key
}

resource "yandex_compute_instance" "bootstrap" {
  name        = "bootstrap"
  platform_id = var.platform_id
  folder_id   = local.folder_id
  hostname    = "bootstrap"
  zone        = yandex_vpc_subnet.this.zone

  resources {
    cores  = 4
    memory = 16
  }
  boot_disk {
    initialize_params {
      image_id = var.image_id
      type     = "network-ssd"
      size     = "120"
    }
  }
  network_interface {
    nat       = true
    subnet_id = yandex_vpc_subnet.this.id
  }
  scheduling_policy {
    preemptible = var.scheduling_policy
  }
  metadata = {
    serial-port-enable = 1
    user-data          = jsonencode({ "ignition" : { "config" : { "replace" : { "source" : "https://${yandex_storage_bucket.ignition.bucket_domain_name}/bootstrap.ign" } }, "version" : "3.1.0" } })
  }
}


resource "yandex_compute_instance" "master" {
  name                      = var.master_name
  platform_id               = var.platform_id
  folder_id                 = local.folder_id
  hostname                  = var.master_name
  zone                      = yandex_vpc_subnet.this.zone
  allow_stopping_for_update = true
  resources {
    cores  = var.master_cpu
    memory = var.master_ram
  }

  boot_disk {
    initialize_params {
      image_id = var.image_id
      type     = var.master_type_disk
      size     = var.size_disk_master_node
    }
  }
  network_interface {
    nat       = true
    subnet_id = yandex_vpc_subnet.this.id
  }
  scheduling_policy {
    preemptible = var.scheduling_policy
  }
  metadata = {
    serial-port-enable = 1
    user-data          = "${file("../okd-ignition/master.ign")}"
  }
}