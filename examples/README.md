# Configuration Examples

This directory contains example configuration files and code examples for OVH OpenStack deployment automation.

## Files

### Configuration Files

#### config.yaml
Complete example configuration demonstrating all available options:
- Multiple instances with metadata
- Network with subnet configuration
- Security groups with multiple rules
- Volumes with attachment specifications
- User data for instance initialization

#### config.json
Same configuration as `config.yaml` but in JSON format. Use this if you prefer JSON over YAML.

#### minimal-config.yaml
Minimal configuration example showing the simplest possible deployment:
- Single instance
- Single network with one subnet
- Basic security group with SSH access

### Code Examples

#### auth_example.py
Demonstrates authentication and connection management:
- Loading credentials from environment variables
- Loading credentials from files
- Creating and managing OpenStack connections
- Token refresh handling

#### network_example.py
Demonstrates network infrastructure creation:
- Creating networks with multiple subnets
- CIDR validation and overlap checking
- Network status verification
- Network name uniqueness enforcement
- Listing and looking up networks

## Environment Variables

All example configurations use environment variables for sensitive credentials:

```bash
export OS_AUTH_URL="https://auth.cloud.ovh.net/v3"
export OS_USERNAME="your-username"
export OS_PASSWORD="your-password"
export OS_TENANT_NAME="your-tenant-name"
export OS_REGION_NAME="GRA7"
```

## Running Examples

### Authentication Example

```bash
# Set environment variables first
export OS_AUTH_URL="https://auth.cloud.ovh.net/v3"
export OS_USERNAME="your-username"
export OS_PASSWORD="your-password"
export OS_TENANT_NAME="your-tenant"
export OS_REGION_NAME="GRA7"

# Run the example
python examples/auth_example.py
```

### Network Infrastructure Example

```bash
# Set environment variables (same as above)
# Then run the network example
python examples/network_example.py
```

This will:
1. Authenticate to OVH OpenStack
2. Create two networks with multiple subnets
3. Verify networks reach ACTIVE state
4. List all networks in the project
5. Demonstrate network lookup by name

**Note:** The example creates real resources in your OVH account. Remember to delete them manually if you don't need them.

## Usage

### With Configuration Manager

```python
from config import ConfigurationManager

# Load configuration
manager = ConfigurationManager()
config = manager.load_config('examples/config.yaml')

# Validate configuration
validation_result = manager.validate_config(config)
if validation_result.is_valid:
    print("Configuration is valid!")
else:
    print("Validation errors:")
    for error in validation_result.errors:
        print(f"  - {error}")
```

### With Network Manager

```python
from openstack_sdk import AuthenticationManager, ConnectionManager, NetworkManager
from config.models import NetworkSpec, SubnetSpec

# Authenticate
auth_manager = AuthenticationManager()
credentials = auth_manager.load_credentials_from_env()

# Create connection
conn_manager = ConnectionManager(credentials)
conn = conn_manager.connect()

# Create network infrastructure
network_manager = NetworkManager(conn)
network_spec = NetworkSpec(
    name="my-network",
    subnets=[
        SubnetSpec(
            name="my-subnet",
            cidr="192.168.1.0/24",
            ip_version=4
        )
    ]
)

networks = network_manager.create_network_infrastructure([network_spec])
```

### Customization

To create your own configuration:

1. Copy one of the example files
2. Update authentication parameters (or set environment variables)
3. Modify resource specifications to match your requirements
4. Validate the configuration before deployment

## Configuration Reference

### Required Fields

- `auth_url`: OVH OpenStack authentication URL
- `username`: OpenStack username
- `password`: OpenStack password
- `tenant_name`: OpenStack tenant/project name
- `region`: OVH region (e.g., "GRA7", "BHS5", "DE1")
- `project_name`: Project identifier
- `instances`: At least one instance specification

### Instance Specification

```yaml
instances:
  - name: "instance-name"          # Required: unique instance name
    flavor: "s1-4"                 # Required: OVH flavor (s1-2, s1-4, s1-8, etc.)
    image: "Ubuntu 22.04"          # Required: OS image name
    key_name: "my-ssh-key"         # Required: SSH key name
    network_ids: ["network-name"]  # Required: list of network names
    security_groups: ["sg-name"]   # Optional: list of security group names
    user_data: "#!/bin/bash..."    # Optional: cloud-init script
    metadata:                      # Optional: key-value metadata
      key: "value"
```

### Network Specification

```yaml
networks:
  - name: "network-name"           # Required: unique network name
    admin_state_up: true           # Optional: default true
    external: false                # Optional: default false
    subnets:                       # Required for private networks
      - name: "subnet-name"        # Required: subnet name
        cidr: "192.168.1.0/24"     # Required: CIDR notation
        ip_version: 4              # Optional: 4 or 6, default 4
        enable_dhcp: true          # Optional: default true
        gateway_ip: "192.168.1.1"  # Optional: gateway IP
        dns_nameservers:           # Optional: DNS servers
          - "8.8.8.8"
```

### Security Group Specification

```yaml
security_groups:
  - name: "sg-name"                # Required: unique security group name
    description: "Description"     # Required: security group description
    rules:                         # Optional: list of rules
      - direction: "ingress"       # Required: ingress or egress
        protocol: "tcp"            # Required: tcp, udp, icmp, or any
        port_range_min: 22         # Optional: minimum port
        port_range_max: 22         # Optional: maximum port
        remote_ip_prefix: "0.0.0.0/0"  # Required: CIDR notation
        ethertype: "IPv4"          # Optional: IPv4 or IPv6, default IPv4
```

### Volume Specification

```yaml
volumes:
  - name: "volume-name"            # Required: unique volume name
    size: 100                      # Required: size in GB
    volume_type: "classic"         # Optional: classic or high-speed
    bootable: false                # Optional: default false
    image_id: "image-id"           # Required if bootable is true
    attach_to: "instance-name"     # Optional: instance to attach to
```

## OVH-Specific Information

### Available Regions
- GRA7 (Gravelines, France)
- BHS5 (Beauharnois, Canada)
- DE1 (Frankfurt, Germany)
- UK1 (London, UK)
- WAW1 (Warsaw, Poland)
- SBG5 (Strasbourg, France)

### Common Flavors
- s1-2: 1 vCore, 2GB RAM
- s1-4: 1 vCore, 4GB RAM
- s1-8: 2 vCores, 8GB RAM
- s1-16: 4 vCores, 16GB RAM

### Volume Types
- classic: Standard performance
- high-speed: High-performance SSD

For more information, visit: https://www.ovhcloud.com/en/public-cloud/
