# Network Infrastructure Outputs

output "network_id" {
  description = "The ID of the created private network"
  value       = openstack_networking_network_v2.private_network.id
}

output "network_name" {
  description = "The name of the created private network"
  value       = openstack_networking_network_v2.private_network.name
}

output "subnet_id" {
  description = "The ID of the created subnet"
  value       = openstack_networking_subnet_v2.private_subnet.id
}

output "subnet_cidr" {
  description = "The CIDR range of the created subnet"
  value       = openstack_networking_subnet_v2.private_subnet.cidr
}

# Security Group Outputs
#
#output "security_group_id" {
#  description = "The ID of the created security group"
#  value       = openstack_networking_secgroup_v2.default_sg.id
#}
#
#output "security_group_name" {
#  description = "The name of the created security group"
#  value       = openstack_networking_secgroup_v2.default_sg.name
#}
#
#output "security_group_rules" {
#  description = "The rules configured in the security group"
#  value       = openstack_networking_secgroup_v2.default_sg.rule
#}

# Compute Instance Outputs

output "instance_ids" {
  description = "List of IDs for all created compute instances"
  value       = openstack_compute_instance_v2.instance[*].id
}

output "instance_names" {
  description = "List of names for all created compute instances"
  value       = openstack_compute_instance_v2.instance[*].name
}

output "instance_ips" {
  description = "List of IP addresses for all created compute instances"
  value       = openstack_compute_instance_v2.instance[*].access_ip_v4
}

output "instance_count" {
  description = "Total number of compute instances created"
  value       = length(openstack_compute_instance_v2.instance)
}

# Storage Volume Outputs

output "volume_ids" {
  description = "List of IDs for all created block storage volumes"
  value       = openstack_blockstorage_volume_v3.volume[*].id
}

output "volume_names" {
  description = "List of names for all created block storage volumes"
  value       = openstack_blockstorage_volume_v3.volume[*].name
}

output "volume_count" {
  description = "Total number of volumes created"
  value       = length(openstack_blockstorage_volume_v3.volume)
}

output "volume_attachments" {
  description = "List of volume attachment IDs"
  value       = openstack_compute_volume_attach_v2.volume_attachment[*].id
}

output "attached_volume_count" {
  description = "Total number of volumes attached to instances"
  value       = length(openstack_compute_volume_attach_v2.volume_attachment)
}

output "volume_attachment_details" {
  description = "Detailed information about volume attachments (instance ID, volume ID, attachment ID)"
  value = [
    for attachment in openstack_compute_volume_attach_v2.volume_attachment : {
      attachment_id = attachment.id
      instance_id   = attachment.instance_id
      volume_id     = attachment.volume_id
      device        = attachment.device
    }
  ]
}

# Comprehensive Deployment Summary

output "deployment_summary" {
  description = "Complete summary of all deployed resources"
  value = {
    network = {
      id   = openstack_networking_network_v2.private_network.id
      name = openstack_networking_network_v2.private_network.name
    }
    subnet = {
      id   = openstack_networking_subnet_v2.private_subnet.id
      cidr = openstack_networking_subnet_v2.private_subnet.cidr
    }
    #security_group = {
    #  id   = openstack_networking_secgroup_v2.default_sg.id
    #  name = openstack_networking_secgroup_v2.default_sg.name
    #}
    instances = {
      count = length(openstack_compute_instance_v2.instance)
      ids   = openstack_compute_instance_v2.instance[*].id
      names = openstack_compute_instance_v2.instance[*].name
      ips   = openstack_compute_instance_v2.instance[*].access_ip_v4
    }
    volumes = {
      count = length(openstack_blockstorage_volume_v3.volume)
      ids   = openstack_blockstorage_volume_v3.volume[*].id
      names = openstack_blockstorage_volume_v3.volume[*].name
    }
    attachments = {
      count = length(openstack_compute_volume_attach_v2.volume_attachment)
      ids   = openstack_compute_volume_attach_v2.volume_attachment[*].id
    }
  }
}
