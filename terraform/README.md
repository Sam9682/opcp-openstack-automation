# Terraform Deployment Solution

This directory contains the Terraform-based deployment solution for OVH OpenStack infrastructure.

## Overview

The Terraform solution provides Infrastructure as Code (IaC) capabilities for deploying and managing OVH OpenStack resources. It uses declarative configuration to define the desired state of infrastructure.

## installation Ubuntu

sudo snap install terraform --classic

## Requirements

- Terraform >= 1.5.0
- terraform-provider-openstack >= 1.51.0
- Valid OVH OpenStack credentials

## Structure

```
terraform/
├── main.tf           # Main Terraform configuration
├── variables.tf      # Input variable definitions
├── outputs.tf        # Output value definitions
├── versions.tf       # Provider version constraints
├── terraform.tfvars  # Variable values (not committed to git)
└── modules/          # Reusable Terraform modules
```

## Usage

### Initialize Terraform

```bash
cd terraform
terraform init
```

### Plan Deployment

```bash
terraform plan -var-file="terraform.tfvars"
```

### Apply Deployment

```bash
terraform apply -var-file="terraform.tfvars"
```

### Destroy Infrastructure

```bash
terraform destroy -var-file="terraform.tfvars"
```

## Configuration

Create a `terraform.tfvars` file with your credentials:

```



```

**Important:** Add `terraform.tfvars` to `.gitignore` to avoid committing credentials.

## Features

- Declarative infrastructure definition
- State management with terraform.tfstate
- Dependency resolution and parallel resource creation
- Idempotent operations
- Plan preview before applying changes
- Network infrastructure (networks and subnets)
- Security groups with configurable rules (SSH, HTTP, HTTPS)
- CIDR validation for network and security group configurations
- Compute instance deployment with configurable count
- Block storage volume creation and attachment
- Automatic dependency management between resources

## Security Groups

The Terraform configuration includes security group resources with the following features:

### Default Rules

- **SSH (Port 22)**: Configurable CIDR range via `allow_ssh_from` variable
- **HTTP (Port 80)**: Optional, controlled by `allow_http` variable
- **HTTPS (Port 443)**: Optional, controlled by `allow_https` variable

### Configuration Variables

```hcl
# Security group name and description
security_group_name        = "my-security-group"
security_group_description = "Security group for web servers"

# SSH access control (CIDR validation enforced)
allow_ssh_from = "203.0.113.0/24"  # Restrict to specific IP range

# Enable/disable HTTP and HTTPS
allow_http  = true
allow_https = true
```

### CIDR Validation

The configuration includes validation constraints to ensure:
- `allow_ssh_from` must be valid CIDR notation
- `subnet_cidr` must be valid CIDR notation
- Invalid CIDR values will cause Terraform to fail during validation

### Security Best Practices

For production deployments:
1. Restrict SSH access to known IP ranges (avoid `0.0.0.0/0`)
2. Use separate security groups for different application tiers
3. Only enable required ports (HTTP/HTTPS)
4. Regularly audit security group rules

## Compute Instances

The Terraform configuration creates compute instances with the following features:

### Configuration Variables

```hcl
# Instance configuration
instance_count    = 3                    # Number of instances to create
instance_flavor   = "s1-4"               # Instance size (CPU/RAM)
instance_image    = "Ubuntu 22.04"       # Operating system image
key_name          = "my-ssh-key"         # SSH key for access

# Optional: Instance metadata and user data
instance_metadata = {
  environment = "production"
  project     = "web-app"
}

instance_user_data = <<-EOF
  #!/bin/bash
  apt-get update
  apt-get install -y nginx
EOF
```

### Features

- Count-based instance creation
- Automatic network attachment
- Security group application
- Metadata tagging support
- Cloud-init user data injection
- Dependency management ensures network and security groups are created first

## Block Storage Volumes

The Terraform configuration creates and attaches block storage volumes to instances:

### Configuration Variables

```hcl
# Volume configuration
volume_count = 3           # Number of volumes to create
volume_size  = 100         # Size in GB
volume_type  = "classic"   # Volume type (classic, high-speed)
```

### Features

- Configurable volume size and type
- Automatic volume attachment to instances
- One-to-one mapping between volumes and instances (up to min(volume_count, instance_count))
- Dependency management ensures instances are active before volume attachment
- Volumes are created in parallel for efficiency

### Volume Attachment Behavior

- If `volume_count` equals `instance_count`: Each instance gets one volume
- If `volume_count` < `instance_count`: First N instances get volumes
- If `volume_count` > `instance_count`: Only instance_count volumes are attached, remaining volumes stay unattached
- Volumes are attached in order: volume-1 → instance-1, volume-2 → instance-2, etc.

## Outputs

After successful deployment, Terraform provides the following outputs:

### Network Outputs
- `network_id`: ID of the created network
- `network_name`: Name of the created network
- `subnet_id`: ID of the created subnet
- `subnet_cidr`: CIDR range of the subnet

### Security Group Outputs
- `security_group_id`: ID of the security group
- `security_group_name`: Name of the security group
- `security_group_rules`: Configured security rules

### Instance Outputs
- `instance_ids`: List of all instance IDs
- `instance_names`: List of all instance names
- `instance_ips`: List of instance IP addresses
- `instance_count`: Total number of instances created

### Volume Outputs
- `volume_ids`: List of all volume IDs
- `volume_names`: List of all volume names
- `volume_count`: Total number of volumes created
- `volume_attachments`: List of volume attachment IDs
- `attached_volume_count`: Number of volumes attached to instances
