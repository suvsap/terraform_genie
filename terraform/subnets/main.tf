resource "google_compute_subnetwork" "subnet1" {
  name          = "subnet-1"
  ip_cidr_range = "10.240.0.0/24"
  region        = "us-west1"
  network       = google_compute_network.vpc_network.name
}

resource "google_compute_subnetwork" "subnet2" {
  name          = "subnet-2"
  ip_cidr_range = "192.168.1.0/24"
  region        = "us-east1"
  network       = google_compute_network.vpc_network.name
}

resource "google_compute_subnetwork" "subnet3" {
  name          = "subnet-3"
  ip_cidr_range = "10.2.0.0/16"
  region        = "us-east1"
  network       = google_compute_network.vpc_network.name
}
