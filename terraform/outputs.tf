output "master-ip-nat" {
  description = "master-ip-nat"
  value       = yandex_compute_instance.master.network_interface[0].nat_ip_address
}
output "master-id" {
  description = "master-id-node"
  value       = yandex_compute_instance.master.id
}