output "subnet_ids" {
  value = [
    google_compute_subnetwork.subnet1.id,
    google_compute_subnetwork.subnet2.id,
    google_compute_subnetwork.subnet3.id
  ]
}
