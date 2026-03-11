# OVH OpenStack Deployment Automation

Automated deployment system for OVH OpenStack private cloud infrastructure with three distinct deployment approaches: Terraform, OpenStack SDK, and Ansible.

## Overview

This project provides multiple solutions for deploying and managing OVH OpenStack infrastructure:

1. **Terraform Solution**: Infrastructure as Code with declarative configuration
2. **OpenStack SDK Solution**: Programmatic Python-based deployment
3. **Ansible Solution**: Configuration management with idempotent playbooks

All solutions share a common configuration format and support the same resource types:
- Compute instances
- Networks and subnets
- Storage volumes
- Security groups
- Floating IPs

## Project Structure

```
.
├── config/                 # Shared configuration management
│   ├── config_manager.py   # Configuration loader and validator
│   └── models.py           # Data models
├── utils/                  # Utility modules
│   └── logger.py           # Logging infrastructure
├── terraform/              # Terraform deployment solution
├── openstack_sdk/          # OpenStack SDK deployment solution
├── ansible/                # Ansible deployment solution
├── examples/               # Example configuration files
│   ├── config.yaml         # Complete example (YAML)
│   ├── config.json         # Complete example (JSON)
│   └── minimal-config.yaml # Minimal example
├── requirements.txt        # Python dependencies
└── requirements-dev.txt    # Development dependencies
```

## Quick Start

### Prerequisites

- Python >= 3.8
- Valid OVH OpenStack account with credentials
- SSH key registered in OVH OpenStack

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ovh-openstack-deployment
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
export OS_USERNAME="your-username"
export OS_PASSWORD="your-password"
export OS_TENANT_NAME="your-tenant-name"
```

### Configuration

Create a configuration file based on the examples:

```bash
cp examples/minimal-config.yaml my-config.yaml
# Edit my-config.yaml with your settings
```

### Validate Configuration

```python
from config import ConfigurationManager

manager = ConfigurationManager()
config = manager.load_config('my-config.yaml')
validation = manager.validate_config(config)

if validation.is_valid:
    print("Configuration is valid!")
else:
    print("Validation errors:")
    for error in validation.errors:
        print(f"  - {error}")
```

## Configuration Format

The system uses a unified configuration format (YAML or JSON) for all deployment solutions:

```yaml
# Authentication
auth_url: "https://auth.cloud.ovh.net/v3"
username: "${OS_USERNAME}"
password: "${OS_PASSWORD}"
tenant_name: "${OS_TENANT_NAME}"
region: "GRA7"
project_name: "my-project"

# Networks
networks:
  - name: "private-network"
    subnets:
      - name: "private-subnet"
        cidr: "192.168.1.0/24"

# Security Groups
security_groups:
  - name: "web-sg"
    description: "Web server security group"
    rules:
      - direction: "ingress"
        protocol: "tcp"
        port_range_min: 22
        port_range_max: 22
        remote_ip_prefix: "0.0.0.0/0"

# Instances
instances:
  - name: "web-server-1"
    flavor: "s1-4"
    image: "Ubuntu 22.04"
    key_name: "my-ssh-key"
    network_ids: ["private-network"]
    security_groups: ["web-sg"]

# Volumes
volumes:
  - name: "data-volume-1"
    size: 100
    volume_type: "classic"
    attach_to: "web-server-1"
```

See `examples/README.md` for complete configuration reference.

## Deployment Solutions

### Terraform Solution

Infrastructure as Code with state management and dependency resolution.

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

See `terraform/README.md` for details.

### OpenStack SDK Solution

Programmatic Python deployment with fine-grained control.

```python
from config import ConfigurationManager
from openstack_sdk.deployment_engine import OpenStackDeploymentEngine

manager = ConfigurationManager()
config = manager.load_config('my-config.yaml')

engine = OpenStackDeploymentEngine(config)
result = engine.deploy_infrastructure()
```

See `openstack_sdk/README.md` for details.

### Ansible Solution

Configuration management with idempotent playbooks.

```bash
ansible-playbook ansible/playbook.yml -e @vars.yml
```

See `ansible/README.md` for details.

## Features

### Configuration Management
- ✅ YAML and JSON configuration support
- ✅ Environment variable substitution
- ✅ Comprehensive validation with descriptive errors
- ✅ Data models for all resource types

### Logging
- ✅ Structured logging with timestamps
- ✅ Configurable log levels (DEBUG, INFO, WARNING, ERROR)
- ✅ File and console output
- ✅ Deployment-specific logging methods

### Security
- Environment variable support for credentials
- No hardcoded credentials
- Secure credential handling
- Security group configuration

### Resource Management
- Networks and subnets
- Compute instances
- Storage volumes
- Security groups
- Floating IPs (coming soon)

## Development

### Install Development Dependencies

```bash
pip install -r requirements-dev.txt
```

### Run Tests

```bash
pytest tests/ -v --cov=config --cov=utils
```

### Code Quality

```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy config/ utils/
```

## Documentation

- `examples/README.md` - Configuration examples and reference
- `terraform/README.md` - Terraform solution documentation
- `openstack_sdk/README.md` - OpenStack SDK solution documentation
- `ansible/README.md` - Ansible solution documentation

## Requirements

### Core Requirements
- Python >= 3.8
- openstacksdk >= 1.0.0
- PyYAML >= 6.0

### Terraform Solution
- Terraform >= 1.5.0
- terraform-provider-openstack >= 1.51.0

### Ansible Solution
- Ansible >= 2.14.0
- openstack.cloud collection >= 2.0.0

See `requirements.txt` and `requirements-dev.txt` for complete dependency lists.

## OVH OpenStack Information

### Available Regions
- GRA7 (Gravelines, France)
- BHS5 (Beauharnois, Canada)
- DE1 (Frankfurt, Germany)
- UK1 (London, UK)
- WAW1 (Warsaw, Poland)
- SBG5 (Strasbourg, France)

### Common Instance Flavors
- s1-2: 1 vCore, 2GB RAM
- s1-4: 1 vCore, 4GB RAM
- s1-8: 2 vCores, 8GB RAM
- s1-16: 4 vCores, 16GB RAM

### Volume Types
- classic: Standard performance
- high-speed: High-performance SSD

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

## Support

For issues and questions:
- OVH Documentation: https://docs.ovh.com/
- OpenStack Documentation: https://docs.openstack.org/
- Project Issues: [Add issue tracker URL]
