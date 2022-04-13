# YC 
variable "folder_id" {
  type        = string
  default     = null
  description = "Folder-ID where the resources will be created"
}

# Image 
variable "image_id" {
  type        = string
  default     = "fd8u9lgdcukfl03sik2n"
  description = "Fedora CoreOS 34"
}

# Scheduling_policy
variable "scheduling_policy" {
  type        = bool
  default     = false
  description = "discontinuous or continuous type node"
}
# Network
variable "network_name" {
  description = "Name to be used on all network resources as identifier"
  default     = "okd_network"
  type        = string
}

variable "network_description" {
  description = "An optional description of this resource. Provide this property when you create the resource."
  type        = string
  default     = "OKD Container Platform Network"
}

variable "subnets" {
  description = "A set of key/value label pairs to assign."
  type        = map(string)
  default = {
    zone           = "ru-central1-a"
    v4_cidr_blocks = "10.88.1.0/24"
  }
}

#DNS
variable "dns_zone_name" {
  type        = string
  default     = "example."
  description = "Base domain name"
}

variable "cluster_name" {
  type        = string
  default     = "okd4"
  description = "okd cluster name, aka dns level 3 domain name"
}

#Labels
variable "labels" {
  description = "A set of key/value label pairs to assign."
  type        = map(string)
  default = {
    tag        = "okd",
    demo       = "false",
    created_by = "okd-yc-upi"
  }
}

# Bootstrap
variable "bootstrap_count" {
  type        = number
  default     = 1
  description = "Number of bootstrap nodes"
}

# Platform
variable "platform_id" {
  type        = string
  default     = "standard-v3"
  description = "Platform Type"
}

#master resources minimum
variable "master_name" {
  type        = string
  default     = "single-master-okd"
  description = "Master name"
}

variable "master_count" {
  type        = number
  default     = 1
  description = "Number of master nodes"
}
variable "master_cpu" {
  type        = number
  default     = 4
  description = "Number of vCPU for master nodes"
}
variable "master_ram" {
  type        = number
  default     = 16
  description = "Number of vRAM for master nodes"
}

variable "master_type_disk" {
  type        = string
  description = "Type disk HDD/SSD"
  default     = "network-hdd"
}

variable "size_disk_master_node" {
  type        = string
  description = "Size disk master node"
  default     = "120"
}
variable "okd_pullSecret" {
  type        = string
  description = "PullSecret okd"
  default     = "{'auths':{'fake':{'auth': 'bar'}}}"
}