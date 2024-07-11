output "instance_names" {
  value = google_compute_instance.vm_instance[*].name
}
