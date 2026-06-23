provider "openstack" {
  # Authentication is handled via standard OpenStack OS_* environment variables:
  #   OS_AUTH_URL, OS_APPLICATION_CREDENTIAL_ID, OS_APPLICATION_CREDENTIAL_SECRET,
  #   OS_PROJECT_NAME (or OS_TENANT_NAME), OS_REGION_NAME
  #
  # The OpenStack provider reads these automatically from the environment.
  # Just source your credentials file before running terraform:
  #   source set_app_cred_env.sh
}

# Build cloud-init user_data that always creates the student user
locals {
  # Cloud-init script: create user + run custom user_data if provided
  cloud_init_script = <<-CLOUDINIT
#!/bin/bash
# Create user with STUDENT_ID name and set password
useradd -m -s /bin/bash ${var.student_id}
echo '${var.student_id}:${var.student_password}' | chpasswd
usermod -aG sudo ${var.student_id}

${var.instance_user_data != null ? var.instance_user_data : "# No additional user_data script provided"}
CLOUDINIT
}

# Network Infrastructure Resources

# Create private network
resource "openstack_networking_network_v2" "private_network" {
  name           = var.network_name
  admin_state_up = true
}

# Create subnet within the private network
resource "openstack_networking_subnet_v2" "private_subnet" {
  name            = "${var.network_name}-subnet"
  network_id      = openstack_networking_network_v2.private_network.id
  cidr            = var.subnet_cidr
  ip_version      = 4
  dns_nameservers = var.dns_nameservers
  enable_dhcp     = var.enable_dhcp
}

# Compute Instance Resources

# Create compute instances with count-based creation
resource "openstack_compute_instance_v2" "instance" {
  count           = var.instance_count
  name            = "${trimspace(var.network_name)}-instance-${count.index + 1}"
  flavor_name     = var.instance_flavor
  image_name      = var.instance_image
  key_pair        = var.key_name
  # Removed security_groups since there are issues with security group rules in OpenStack provider

  # Attach instance to the private network
  network {
    uuid = openstack_networking_network_v2.private_network.id
  }

  # Apply metadata tags if provided
  metadata = var.instance_metadata

  # Inject user_data script (includes student user creation + custom script)
  user_data = local.cloud_init_script

  # Explicit dependencies to ensure correct creation order
  depends_on = [
    openstack_networking_subnet_v2.private_subnet
    # Removed dependency on security group since it's removed
  ]
}

# Storage Volume Resources

# Create block storage volumes
resource "openstack_blockstorage_volume_v3" "volume" {
  count       = var.volume_count
  name        = "${trimspace(var.network_name)}-volume-${count.index + 1}"
  size        = var.volume_size
  volume_type = var.volume_type

  # Configure bootable volumes if specified
  image_id = var.volume_bootable && var.volume_image_id != null ? var.volume_image_id : null

  # Explicit dependency to ensure network infrastructure is ready
  depends_on = [
    openstack_networking_subnet_v2.private_subnet
  ]
}

# Attach volumes to instances
resource "openstack_compute_volume_attach_v2" "volume_attachment" {
  count       = min(var.volume_count, var.instance_count)
  instance_id = openstack_compute_instance_v2.instance[count.index].id
  volume_id   = openstack_blockstorage_volume_v3.volume[count.index].id

  # Explicit dependency to ensure instances are active before attaching volumes
  depends_on = [
    openstack_compute_instance_v2.instance,
    openstack_blockstorage_volume_v3.volume
  ]
}