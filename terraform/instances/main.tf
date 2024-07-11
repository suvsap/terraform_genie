resource "google_compute_instance" "vm_instance" {
  count        = 6
  name         = "vm-instance-${count.index + 1}"
  machine_type = "n1-standard-1"
  zone         = element(["us-west1-a", "us-east1-a", "us-east1-a", "us-east1-b"], count.index)
  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-9"
    }
  }
  network_interface {
    network    = google_compute_network.vpc_network.name
    subnetwork = element(["subnet-1", "subnet-2", "subnet-2", "subnet-3"], count.index)
  }
}
