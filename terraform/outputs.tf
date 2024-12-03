output "vpc_network" {
  value = module.vpc.network_name
}

output "subnets" {
  value = module.subnets.subnet_ids
}

output "instances" {
  value = module.instances.instance_names
}
