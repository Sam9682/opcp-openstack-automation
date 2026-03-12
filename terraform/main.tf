provider "openstack" {
  auth_url    = var.auth_url
  user_name   = var.username
  password    = var.password
  tenant_name = var.tenant_name
  region      = var.region
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

# Security Group Resources

# Create security group
resource "openstack_compute_secgroup_v2" "default_sg" {
  name        = var.security_group_name
  description = var.security_group_description

  # SSH access rule
  rule {
    from_port   = 22
    to_port     = 22
    ip_protocol = "tcp"
    cidr        = var.allow_ssh_from
  }

  # HTTP access rule (conditional based on variable)
  dynamic "rule" {
    for_each = var.allow_http ? [1] : []
    content {
      from_port   = 80
      to_port     = 80
      ip_protocol = "tcp"
      cidr        = "0.0.0.0/0"
    }
  }

  # HTTPS access rule (conditional based on variable)
  dynamic "rule" {
    for_each = var.allow_https ? [1] : []
    content {
      from_port   = 443
      to_port     = 443
      ip_protocol = "tcp"
      cidr        = "0.0.0.0/0"
    }
  }
}

# Compute Instance Resources

# Create compute instances with count-based creation
resource "openstack_compute_instance_v2" "instance" {
  count           = var.instance_count
  name            = "${var.network_name}-instance-${count.index + 1}"
  flavor_name     = var.instance_flavor
  image_name      = var.instance_image
  key_pair        = var.key_name
  security_groups = [openstack_compute_secgroup_v2.default_sg.name]

  # Attach instance to the private network
  network {
    uuid = openstack_networking_network_v2.private_network.id
  }

  # Apply metadata tags if provided
  metadata = var.instance_metadata

  # Inject user_data script if provided
  user_data = var.instance_user_data

  # Explicit dependencies to ensure correct creation order
  depends_on = [
    openstack_networking_subnet_v2.private_subnet,
    openstack_compute_secgroup_v2.default_sg
  ]
}

# Storage Volume Resources

# Create block storage volumes
resource "openstack_blockstorage_volume_v3" "volume" {
  count       = var.volume_count
  name        = "${var.network_name}-volume-${count.index + 1}"
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
