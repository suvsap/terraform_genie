provider "google" {
  project = var.project_id
  region  = var.region
}

module "vpc" {
  source = "./vpc"
}

module "subnets" {
  source = "./subnets"
}

module "instances" {
  source = "./instances"
}
}
