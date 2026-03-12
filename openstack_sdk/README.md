# OpenStack SDK Deployment Solution

This directory contains the OpenStack SDK-based deployment solution for OVH OpenStack infrastructure.

## Overview

The OpenStack SDK solution provides programmatic Python-based deployment capabilities. It offers fine-grained control over resource creation and management through the OpenStack Python SDK.

## Requirements

- Python >= 3.8
- openstacksdk >= 1.0.0
- Valid OVH OpenStack credentials

## Structure

```
openstack_sdk/
├── __init__.py          # Package initialization
├── auth_manager.py      # Authentication and connection management
├── deployment_engine.py # Main deployment engine (coming soon)
├── network_manager.py   # Network resource management (coming soon)
├── compute_manager.py   # Compute instance management (coming soon)
├── volume_manager.py    # Volume management (coming soon)
├── security_manager.py  # Security group management (coming soon)
└── utils.py            # Utility functions (coming soon)
```

## Authentication and Connection Management

The `auth_manager` module provides secure authentication and connection management for OVH OpenStack.

### Features

- **Multiple credential sources**: Load from environment variables or secure files
- **Automatic token refresh**: Handles token expiration during long-running deployments
- **Secure credential handling**: Never logs passwords or tokens
- **Connection lifecycle management**: Proper connection creation and cleanup
- **Context manager support**: Use with Python's `with` statement

### Usage Examples

#### 1. Load Credentials from Environment Variables

```python
from openstack_sdk.auth_manager import AuthenticationManager

# Create authentication manager
auth_manager = AuthenticationManager()

# Load credentials from environment variables
# Requires: OS_AUTH_URL, OS_USERNAME, OS_PASSWORD, OS_TENANT_NAME, OS_REGION_NAME
credentials = auth_manager.load_credentials_from_env()

# Authenticate and create connection
connection = auth_manager.authenticate(credentials)

# Use connection...
projects = list(connection.identity.projects())

# Close connection
connection.close()
```

#### 2. Load Credentials from File

```python
from openstack_sdk.auth_manager import AuthenticationManager

auth_manager = AuthenticationManager()

# Load from secure file (should have 600 permissions)
credentials = auth_manager.load_credentials_from_file('path/to/credentials.txt')

# Authenticate
connection = auth_manager.authenticate(credentials)
```

#### 3. Use ConnectionManager for Automatic Token Refresh

```python
from openstack_sdk.auth_manager import ConnectionManager
from config.models import AuthCredentials

# Create credentials
credentials = AuthCredentials(
    auth_url='https://auth.cloud.ovh.net/v3',
    username='your-username',
    password='your-password',
    tenant_name='your-tenant',
    region='GRA7',
    project_name='your-tenant'
)

# Create connection manager
conn_manager = ConnectionManager(credentials)

# Get connection (automatically refreshes token if needed)
connection = conn_manager.get_connection()

# Use connection for long-running operations
# Token will be automatically refreshed if it approaches expiry

# Close when done
conn_manager.close()
```

#### 4. Use as Context Manager

```python
from openstack_sdk.auth_manager import ConnectionManager

conn_manager = ConnectionManager(credentials)

# Connection is automatically closed when exiting the context
with conn_manager as connection:
    # Use connection
    projects = list(connection.identity.projects())
    print(f"Found {len(projects)} projects")
```

### Credential File Format

Create a file with key=value pairs:

```
OS_AUTH_URL=https://auth.cloud.ovh.net/v3
OS_USERNAME=your-username
OS_PASSWORD=your-password
OS_TENANT_NAME=your-tenant
OS_REGION_NAME=GRA7
```

**Security Note**: Set file permissions to 600:
```bash
chmod 600 credentials.txt
```

### Environment Variables

Set these environment variables for credential loading:

```bash
export OS_AUTH_URL=https://auth.cloud.ovh.net/v3
export OS_USERNAME=your-username
export OS_PASSWORD=your-password
export OS_TENANT_NAME=your-tenant
export OS_REGION_NAME=GRA7
```

### Error Handling

The authentication module raises `AuthenticationError` for authentication failures:

```python
from openstack_sdk.auth_manager import AuthenticationManager, AuthenticationError

auth_manager = AuthenticationManager()

try:
    credentials = auth_manager.load_credentials_from_env()
    connection = auth_manager.authenticate(credentials)
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
    # Handle error appropriately
```

### Token Refresh

The `ConnectionManager` automatically refreshes authentication tokens when they approach expiry (default: 5 minutes before expiration). This ensures long-running deployments don't fail due to expired tokens.

```python
# Token refresh happens automatically
conn_manager = ConnectionManager(credentials)

# This connection will remain valid even for long operations
connection = conn_manager.get_connection()

# Perform long-running deployment...
# Token is automatically refreshed if needed
```

## Full Deployment Example

```python
from config import ConfigurationManager
from openstack_sdk.auth_manager import ConnectionManager

# Load configuration
config_manager = ConfigurationManager()
config = config_manager.load_config('examples/config.yaml')

# Validate configuration
validation = config_manager.validate_config(config)
if not validation.is_valid:
    print("Configuration errors:", validation.errors)
    exit(1)

# Get credentials
credentials = config_manager.get_auth_credentials(config)

# Create connection manager
conn_manager = ConnectionManager(credentials)

try:
    # Get connection
    connection = conn_manager.get_connection()
    
    # Deploy infrastructure (coming soon)
    # result = deploy_infrastructure(connection, config)
    
finally:
    # Always close connection
    conn_manager.close()
```

## Security Best Practices

1. **Never hardcode credentials** in source code
2. **Use environment variables** or secure credential files
3. **Set file permissions** to 600 for credential files
4. **Never commit credentials** to version control
5. **Use application credentials** instead of user passwords when possible
6. **Rotate credentials** regularly
7. **Enable MFA** on your OVH account

## Testing

Run the authentication module tests:

```bash
pytest tests/test_auth_manager.py -v
```

## Network Infrastructure Management

The `network_manager` module provides network and subnet creation with comprehensive validation.

### Features

- **Network creation**: Create virtual networks with specified configurations
- **Subnet management**: Create subnets with CIDR validation
- **CIDR validation**: Validate CIDR notation and check for overlaps
- **Name uniqueness**: Enforce unique network names within deployments
- **Status verification**: Ensure networks reach ACTIVE state

See `examples/network_example.py` for usage examples.

## Security Group Management

The `security_group_manager` module provides security group and rule creation with comprehensive validation.

### Features

- **Security group creation**: Create security groups with descriptions
- **Rule validation**: Validate direction, protocol, ports, and CIDR
- **Port range validation**: Ensure port_range_min <= port_range_max
- **CIDR validation**: Validate remote_ip_prefix CIDR notation
- **Protocol support**: TCP, UDP, ICMP, and any protocol
- **IPv4/IPv6 support**: Support for both IPv4 and IPv6 rules
- **Name uniqueness**: Enforce unique security group names

### Usage Examples

#### 1. Create Security Groups

```python
from openstack_sdk.auth_manager import AuthManager
from openstack_sdk.security_group_manager import SecurityGroupManager
from config.models import SecurityGroupSpec, SecurityGroupRule

# Authenticate
auth_manager = AuthManager(
    auth_url='https://auth.cloud.ovh.net/v3',
    username='your-username',
    password='your-password',
    tenant_name='your-tenant',
    region='GRA7',
    project_name='your-project'
)
connection = auth_manager.get_connection()

# Create security group manager
sg_manager = SecurityGroupManager(connection)

# Define security group
web_sg = SecurityGroupSpec(
    name="web-server-sg",
    description="Security group for web servers",
    rules=[
        SecurityGroupRule(
            direction="ingress",
            protocol="tcp",
            port_range_min=22,
            port_range_max=22,
            remote_ip_prefix="0.0.0.0/0",
            ethertype="IPv4"
        ),
        SecurityGroupRule(
            direction="ingress",
            protocol="tcp",
            port_range_min=80,
            port_range_max=80,
            remote_ip_prefix="0.0.0.0/0",
            ethertype="IPv4"
        ),
        SecurityGroupRule(
            direction="ingress",
            protocol="tcp",
            port_range_min=443,
            port_range_max=443,
            remote_ip_prefix="0.0.0.0/0",
            ethertype="IPv4"
        )
    ]
)

# Create security groups
created_groups = sg_manager.create_security_groups([web_sg])
print(f"Created security group: {created_groups[0].id}")
```

#### 2. Create Database Security Group (Private Network Only)

```python
db_sg = SecurityGroupSpec(
    name="database-sg",
    description="Security group for database servers",
    rules=[
        # PostgreSQL from private network only
        SecurityGroupRule(
            direction="ingress",
            protocol="tcp",
            port_range_min=5432,
            port_range_max=5432,
            remote_ip_prefix="192.168.1.0/24",
            ethertype="IPv4"
        ),
        # MySQL from private network only
        SecurityGroupRule(
            direction="ingress",
            protocol="tcp",
            port_range_min=3306,
            port_range_max=3306,
            remote_ip_prefix="192.168.1.0/24",
            ethertype="IPv4"
        )
    ]
)

created_groups = sg_manager.create_security_groups([db_sg])
```

#### 3. Create ICMP Rule

```python
icmp_rule = SecurityGroupRule(
    direction="ingress",
    protocol="icmp",
    remote_ip_prefix="10.0.0.0/8",
    ethertype="IPv4"
)

# Add to security group
sg_manager.create_security_group_rule(security_group_id, icmp_rule)
```

#### 4. Create IPv6 Rule

```python
ipv6_rule = SecurityGroupRule(
    direction="ingress",
    protocol="tcp",
    port_range_min=443,
    port_range_max=443,
    remote_ip_prefix="::/0",
    ethertype="IPv6"
)

sg_manager.create_security_group_rule(security_group_id, ipv6_rule)
```

#### 5. Query Security Groups

```python
# Get security group by name
sg = sg_manager.get_security_group_by_name("web-server-sg")
if sg:
    print(f"Found: {sg.name} (ID: {sg.id})")

# List all security groups
all_groups = sg_manager.list_security_groups()
for sg in all_groups:
    print(f"  - {sg.name} (ID: {sg.id})")

# Delete security group
sg_manager.delete_security_group(sg.id)
```

### Rule Validation

The security group manager validates all rule parameters:

- **Direction**: Must be "ingress" or "egress"
- **Protocol**: Must be "tcp", "udp", "icmp", or "any"
- **Ethertype**: Must be "IPv4" or "IPv6"
- **Port ranges**: port_range_min <= port_range_max
- **Port values**: Must be between 0 and 65535
- **CIDR notation**: Must be valid CIDR (e.g., "192.168.1.0/24")

### Error Handling

```python
from openstack_sdk.security_group_manager import SecurityGroupError

try:
    created_groups = sg_manager.create_security_groups(sg_specs)
except SecurityGroupError as e:
    print(f"Security group creation failed: {e}")
```

See `examples/security_group_example.py` for a complete example.

## Compute Instance Management

The `compute_manager` module provides compute instance creation and management with comprehensive validation.

### Features

- **Instance creation**: Create compute instances with specified flavor, image, and configuration
- **Flavor validation**: Validate that specified flavors exist in OVH catalog
- **Image validation**: Validate that specified images exist in OVH catalog
- **Network attachment**: Attach instances to specified networks
- **Security group application**: Apply security groups to instances
- **SSH key configuration**: Configure SSH keys for instance access
- **User data injection**: Inject cloud-init user_data scripts
- **Metadata support**: Attach custom metadata to instances
- **Status polling**: Wait for instances to reach ACTIVE status with timeout (300s)
- **Name uniqueness**: Enforce unique instance names within deployments
- **Resource caching**: Cache flavor and image lookups for performance

### Usage Examples

#### 1. Create Compute Instances

```python
from openstack_sdk.auth_manager import ConnectionManager
from openstack_sdk.compute_manager import ComputeManager
from config.models import InstanceSpec, AuthCredentials

# Authenticate
credentials = AuthCredentials(
    auth_url='https://auth.cloud.ovh.net/v3',
    username='your-username',
    password='your-password',
    tenant_name='your-tenant',
    region='GRA7',
    project_name='your-tenant'
)

conn_manager = ConnectionManager(credentials)
connection = conn_manager.connect()

# Create compute manager
compute_manager = ComputeManager(connection)

# Define instance specifications
instance_specs = [
    InstanceSpec(
        name="web-server-1",
        flavor="s1-2",  # Small instance
        image="Ubuntu 22.04",
        key_name="opcp-automation-my-ssh-key-training-001",
        network_ids=["network-id-123"],
        security_groups=["web-security-group"],
        user_data="""#!/bin/bash
apt-get update
apt-get install -y nginx
systemctl start nginx
""",
        metadata={
            "project": "web-app",
            "environment": "production",
            "role": "web-server"
        }
    ),
    InstanceSpec(
        name="web-server-2",
        flavor="s1-2",
        image="Ubuntu 22.04",
        key_name="opcp-automation-my-ssh-key-training-001",
        network_ids=["network-id-123"],
        security_groups=["web-security-group"],
        metadata={
            "project": "web-app",
            "environment": "production",
            "role": "web-server"
        }
    )
]

# Create instances (waits for ACTIVE status)
instances = compute_manager.create_compute_instances(instance_specs)

for instance in instances:
    print(f"Created: {instance.name} (ID: {instance.id}, Status: {instance.status})")
```

#### 2. Create Instance with Multiple Networks

```python
instance_spec = InstanceSpec(
    name="multi-network-instance",
    flavor="s1-4",
    image="Debian 11",
    key_name="opcp-automation-my-ssh-key-training-001",
    network_ids=[
        "public-network-id",
        "private-network-id"
    ],
    security_groups=["default", "custom-sg"]
)

instances = compute_manager.create_compute_instances([instance_spec])
```

#### 3. Create Instance with Cloud-Init User Data

```python
user_data_script = """#!/bin/bash
# Update system
apt-get update
apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Start application container
docker run -d -p 80:80 nginx:latest

# Configure monitoring
echo "*/5 * * * * /usr/local/bin/health-check.sh" | crontab -
"""

instance_spec = InstanceSpec(
    name="docker-host",
    flavor="s1-8",
    image="Ubuntu 22.04",
    key_name="opcp-automation-my-ssh-key-training-001",
    network_ids=["network-id"],
    security_groups=["docker-sg"],
    user_data=user_data_script,
    metadata={
        "application": "docker-host",
        "auto-scaling": "enabled"
    }
)

instances = compute_manager.create_compute_instances([instance_spec])
```

#### 4. Query and Manage Instances

```python
# Get instance by name
instance = compute_manager.get_instance_by_name("web-server-1")
if instance:
    print(f"Found: {instance.name} (ID: {instance.id}, Status: {instance.status})")

# List all instances
all_instances = compute_manager.list_instances()
for instance in all_instances:
    print(f"  - {instance.name} (ID: {instance.id}, Status: {instance.status})")

# Wait for specific instance to become ACTIVE
instance = compute_manager.wait_for_instance_active("instance-id-123", timeout=300)
print(f"Instance is now {instance.status}")

# Delete instance
success = compute_manager.delete_instance("instance-id-123")
if success:
    print("Instance deleted successfully")
```

#### 5. Create Minimal Instance (No Optional Fields)

```python
# Minimal instance without user_data, metadata, or security groups
minimal_spec = InstanceSpec(
    name="minimal-instance",
    flavor="s1-2",
    image="Ubuntu 22.04",
    key_name="opcp-automation-my-ssh-key-training-001",
    network_ids=["network-id"]
)

instances = compute_manager.create_compute_instances([minimal_spec])
```

### Instance Flavors

Common OVH instance flavors:
- `s1-2`: 1 vCore, 2 GB RAM
- `s1-4`: 1 vCore, 4 GB RAM
- `s1-8`: 2 vCores, 8 GB RAM
- `b2-7`: 2 vCores, 7 GB RAM
- `b2-15`: 4 vCores, 15 GB RAM
- `b2-30`: 8 vCores, 30 GB RAM

### Instance Images

Common OVH images:
- `Ubuntu 22.04`
- `Ubuntu 20.04`
- `Debian 11`
- `Debian 10`
- `CentOS 8`
- `Rocky Linux 8`

### Validation

The compute manager validates:
- **Flavor exists**: Checks flavor is available in OVH catalog
- **Image exists**: Checks image is available in OVH catalog
- **Networks exist**: Validates all specified networks exist
- **Security groups exist**: Validates all specified security groups exist
- **At least one network**: Requires at least one network attachment
- **Name uniqueness**: Ensures instance names are unique within deployment

### Status Polling

The compute manager automatically waits for instances to reach ACTIVE status:
- **Default timeout**: 300 seconds (5 minutes)
- **Polling interval**: 5 seconds
- **Error detection**: Detects ERROR state and reports fault details
- **Concurrent waiting**: Waits for multiple instances in parallel

### Error Handling

```python
from openstack_sdk.compute_manager import ComputeError

try:
    instances = compute_manager.create_compute_instances(instance_specs)
except ComputeError as e:
    print(f"Instance creation failed: {e}")
    # Handle error appropriately
```

Common errors:
- Flavor not found in OVH catalog
- Image not found in OVH catalog
- Network doesn't exist
- Security group doesn't exist
- Instance timeout (didn't reach ACTIVE within 300s)
- Duplicate instance names
- Insufficient quota

### Performance Optimization

The compute manager includes performance optimizations:
- **Flavor caching**: Caches flavor ID lookups to reduce API calls
- **Image caching**: Caches image ID lookups to reduce API calls
- **Parallel status polling**: Checks multiple instance statuses concurrently

See `examples/compute_example.py` for a complete example.

## Volume Management

The `volume_manager` module provides volume creation and attachment with comprehensive validation.

### Features

- **Volume creation**: Create block storage volumes with specified size and type
- **Size validation**: Validate volume size is positive integer
- **Type validation**: Validate volume type is valid for OVH OpenStack
- **Bootable volumes**: Support bootable volumes with image_id
- **Status polling**: Wait for volumes to reach available status with timeout (60s)
- **Volume attachment**: Attach volumes to instances with verification
- **Instance verification**: Verify instances are in ACTIVE status before attachment
- **State transitions**: Verify volume status changes from available to in-use
- **Exponential backoff**: Use exponential backoff for status polling

### Usage Examples

#### 1. Create Standalone Volumes

```python
from openstack_sdk.auth_manager import ConnectionManager
from openstack_sdk.volume_manager import VolumeManager
from config.models import VolumeSpec, AuthCredentials

# Authenticate
credentials = AuthCredentials(
    auth_url='https://auth.cloud.ovh.net/v3',
    username='your-username',
    password='your-password',
    tenant_name='your-tenant',
    region='GRA7',
    project_name='your-tenant'
)

conn_manager = ConnectionManager(credentials)
connection = conn_manager.connect()

# Create volume manager
volume_manager = VolumeManager(connection)

# Define volume specifications
volume_specs = [
    VolumeSpec(
        name="data-volume-1",
        size=100,  # 100 GB
        volume_type="classic"
    ),
    VolumeSpec(
        name="data-volume-2",
        size=200,  # 200 GB
        volume_type="high-speed"
    )
]

# Create volumes (waits for available status)
volumes = volume_manager.create_and_attach_volumes(volume_specs, {})

for volume in volumes:
    print(f"Created: {volume.name} (ID: {volume.id}, Status: {volume.status})")
```

#### 2. Create Bootable Volume

```python
# Create bootable volume with image
bootable_volume = VolumeSpec(
    name="boot-volume",
    size=50,  # 50 GB
    volume_type="high-speed",
    bootable=True,
    image_id="image-id-123"  # Replace with actual image ID
)

volumes = volume_manager.create_and_attach_volumes([bootable_volume], {})
print(f"Created bootable volume: {volumes[0].name}")
```

#### 3. Create and Attach Volumes to Instances

```python
from openstack_sdk.compute_manager import ComputeManager

# First, create or get instances
compute_manager = ComputeManager(connection)
instances = compute_manager.list_instances()

# Create dictionary mapping instance names to Server objects
instances_dict = {inst.name: inst for inst in instances}

# Define volumes to attach
volume_specs = [
    VolumeSpec(
        name="web-server-1-data",
        size=150,
        volume_type="classic",
        attach_to="web-server-1"  # Instance name
    ),
    VolumeSpec(
        name="web-server-2-data",
        size=150,
        volume_type="classic",
        attach_to="web-server-2"
    )
]

# Create and attach volumes
volumes = volume_manager.create_and_attach_volumes(volume_specs, instances_dict)

for volume in volumes:
    print(f"Created and attached: {volume.name} (Status: {volume.status})")
```

#### 4. Create Multiple Volume Types

```python
volume_specs = [
    # Standard storage
    VolumeSpec(
        name="standard-volume",
        size=100,
        volume_type="classic"
    ),
    # High-performance storage
    VolumeSpec(
        name="fast-volume",
        size=50,
        volume_type="high-speed"
    ),
    # Large data volume
    VolumeSpec(
        name="large-data-volume",
        size=1000,
        volume_type="classic"
    )
]

volumes = volume_manager.create_and_attach_volumes(volume_specs, {})
```

#### 5. Query and Manage Volumes

```python
# List all volumes
all_volumes = volume_manager.list_volumes()
for volume in all_volumes:
    print(f"  - {volume.name} (ID: {volume.id}, Size: {volume.size}GB, Status: {volume.status})")

# Delete volume
success = volume_manager.delete_volume("volume-id-123")
if success:
    print("Volume deleted successfully")

# Detach volume from instance
success = volume_manager.detach_volume("instance-id", "volume-id")
if success:
    print("Volume detached successfully")
```

### Volume Types

Common OVH volume types:
- `classic`: Standard performance block storage
- `high-speed`: High-performance SSD storage

### Validation

The volume manager validates:
- **Size is positive**: Volume size must be a positive integer
- **Bootable requires image_id**: Bootable volumes must have image_id specified
- **Instance exists**: attach_to must reference an existing instance
- **Instance is ACTIVE**: Instances must be in ACTIVE status before attachment
- **Volume type**: Volume type must be valid for OVH OpenStack

### Status Polling

The volume manager automatically waits for volumes to reach appropriate status:
- **Available timeout**: 60 seconds for volume to become available
- **In-use verification**: 30 seconds to verify volume attached (in-use status)
- **Exponential backoff**: Polling interval increases from 2s to 10s
- **Error detection**: Detects error state and reports immediately

### Volume State Transitions

1. **Creating → Available**: After volume creation
2. **Available → Attaching**: When attachment is initiated
3. **Attaching → In-use**: After successful attachment

### Error Handling

```python
from openstack_sdk.volume_manager import VolumeError

try:
    volumes = volume_manager.create_and_attach_volumes(volume_specs, instances_dict)
except VolumeError as e:
    print(f"Volume operation failed: {e}")
    # Handle error appropriately
```

Common errors:
- Volume size is not positive integer
- Bootable volume missing image_id
- attach_to references non-existent instance
- Instance not in ACTIVE status
- Volume creation timeout (didn't reach available within 60s)
- Volume attachment failed
- Volume didn't reach in-use status after attachment

### Performance Optimization

The volume manager includes performance optimizations:
- **Exponential backoff**: Reduces API calls during status polling
- **Concurrent operations**: Can create multiple volumes in parallel
- **Efficient polling**: Starts with 2s interval, increases to 10s maximum

See `examples/volume_example.py` for a complete example.

## Coming Soon

- Additional deployment features and optimizations

## Deployment Engine

The `deployment_engine` module provides complete infrastructure deployment orchestration with automatic rollback and cleanup capabilities.

### Features

- **Complete orchestration**: Deploys networks, security groups, instances, and volumes in correct dependency order
- **Deployment tracking**: Unique deployment_id for each deployment attempt
- **Automatic rollback**: Rolls back all resources on deployment failure
- **Manual cleanup**: Cleanup function for removing specific resources
- **Error handling**: Comprehensive error handling with try-catch blocks
- **API rate limiting**: Exponential backoff for API rate limit handling
- **Resource caching**: Caches flavors, images, and networks to reduce API calls
- **Performance optimization**: Concurrent operations where possible
- **Detailed results**: Returns comprehensive deployment results with resource IDs

### Usage Examples

#### 1. Complete Infrastructure Deployment

```python
from openstack_sdk import DeploymentEngine, AuthenticationManager
from config.models import (
    DeploymentConfig, NetworkSpec, SubnetSpec,
    SecurityGroupSpec, SecurityGroupRule, InstanceSpec, VolumeSpec
)

# Load credentials
auth_mgr = AuthenticationManager()
credentials = auth_mgr.load_credentials_from_env()

# Create deployment configuration
config = DeploymentConfig(
    auth_url=credentials.auth_url,
    username=credentials.username,
    password=credentials.password,
    tenant_name=credentials.tenant_name,
    region=credentials.region,
    project_name=credentials.tenant_name,
    
    networks=[
        NetworkSpec(
            name="app-network",
            admin_state_up=True,
            external=False,
            subnets=[
                SubnetSpec(
                    name="app-subnet",
                    cidr="192.168.1.0/24",
                    ip_version=4,
                    enable_dhcp=True,
                    dns_nameservers=["8.8.8.8", "8.8.4.4"]
                )
            ]
        )
    ],
    
    security_groups=[
        SecurityGroupSpec(
            name="web-sg",
            description="Web server security group",
            rules=[
                SecurityGroupRule(
                    direction="ingress",
                    protocol="tcp",
                    port_range_min=80,
                    port_range_max=80,
                    remote_ip_prefix="0.0.0.0/0",
                    ethertype="IPv4"
                )
            ]
        )
    ],
    
    instances=[
        InstanceSpec(
            name="web-server",
            flavor="s1-2",
            image="Ubuntu 22.04",
            key_name="my-ssh-key",
            network_ids=[],  # Populated after network creation
            security_groups=["web-sg"],
            metadata={"role": "web"}
        )
    ],
    
    volumes=[
        VolumeSpec(
            name="data-volume",
            size=100,
            volume_type="classic",
            attach_to="web-server"
        )
    ]
)

# Create deployment engine
engine = DeploymentEngine(credentials)

# Deploy infrastructure
result = engine.deploy_infrastructure(config)

if result.success:
    print(f"Deployment successful! ID: {result.deployment_id}")
    print(f"Duration: {result.duration_seconds:.2f}s")
    print("Created resources:")
    for resource_type, ids in result.created_resources.items():
        print(f"  {resource_type}: {len(ids)} resource(s)")
else:
    print(f"Deployment failed! ID: {result.deployment_id}")
    for failed in result.failed_resources:
        print(f"  {failed.resource_type}: {failed.error_message}")
```

#### 2. Manual Resource Cleanup

```python
# Cleanup specific resources
resource_ids = {
    'instances': ['instance-id-1', 'instance-id-2'],
    'volumes': ['volume-id-1'],
    'networks': ['network-id-1']
}

results = engine.cleanup_resources(resource_ids)

for resource_key, success in results.items():
    status = "✓" if success else "✗"
    print(f"{status} {resource_key}")
```

#### 3. Deployment with Error Handling

```python
from openstack_sdk import DeploymentError

try:
    result = engine.deploy_infrastructure(config)
    
    if result.success:
        print(f"Deployment {result.deployment_id} successful")
        # Save deployment ID for later reference
        with open('deployment_id.txt', 'w') as f:
            f.write(result.deployment_id)
    else:
        print(f"Deployment {result.deployment_id} failed")
        if result.orphaned_resources:
            print("Orphaned resources requiring manual cleanup:")
            for orphaned in result.orphaned_resources:
                print(f"  - {orphaned}")

except DeploymentError as e:
    print(f"Deployment error: {e}")
```

### Deployment Result

The `DeploymentResult` object contains:

```python
@dataclass
class DeploymentResult:
    success: bool                              # True if deployment succeeded
    deployment_id: str                         # Unique deployment identifier
    created_resources: Dict[str, List[str]]    # Resource IDs by type
    failed_resources: List[FailedResource]     # Failed resource details
    duration_seconds: float                    # Deployment duration
    timestamp: str                             # ISO 8601 timestamp
    orphaned_resources: List[str]              # Resources that couldn't be cleaned up
```

### Deployment Order

Resources are created in dependency order:

1. **Networks and Subnets**: Created first as instances need networks
2. **Security Groups**: Created before instances that reference them
3. **Compute Instances**: Created after networks and security groups
4. **Volumes**: Created and attached after instances are ACTIVE

### Rollback Behavior

On deployment failure, resources are deleted in reverse dependency order:

1. **Volumes**: Detached and deleted first
2. **Instances**: Deleted after volumes
3. **Security Groups**: Deleted after instances
4. **Subnets**: Deleted after instances
5. **Networks**: Deleted last

### Error Handling

The deployment engine handles:

- **Authentication failures**: Returns error immediately without creating resources
- **Quota exceeded**: Reports quota errors with resource type
- **Network creation failures**: Rolls back and reports network errors
- **Instance timeouts**: Rolls back if instances don't reach ACTIVE within 300s
- **Volume attachment failures**: Rolls back and reports volume errors
- **API rate limiting**: Implements exponential backoff (1s to 60s)

### Performance Optimizations

- **Resource caching**: Caches flavors, images, and networks
- **Exponential backoff**: For status polling (2s to 10s)
- **Concurrent operations**: Where dependencies allow
- **Efficient polling**: Reduces API calls during status checks

### Complete Example

See `examples/deploy_example.py` for a complete deployment example with:
- Credential loading
- Configuration creation
- Deployment execution
- Result handling
- Error handling

```bash
# Run the example
python examples/deploy_example.py
```
