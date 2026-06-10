# Examples Documentation

This directory contains various examples demonstrating how to use the OVH OpenStack Deployment Automation system.

## Authentication Examples

### Basic Authentication Example

The `auth_example.py` script demonstrates different ways to authenticate with OpenStack:

1. **Loading credentials from environment variables** - Most common approach
2. **Loading credentials from a file** - For testing purposes
3. **Using ConnectionManager** - For automatic token refresh
4. **Using ConnectionManager as context manager** - Automatic cleanup

### Application Credentials Example

The `app_cred_example.py` script specifically demonstrates how to use application credentials:

```bash
# Set up environment variables for application credentials
export OS_AUTH_TYPE=v3applicationcredential
export OS_AUTH_URL=https://keystone.demo.bmp.ovhgoldorack.ovh/v3
export OS_IDENTITY_API_VERSION=3
export OS_REGION_NAME="demo"
export OS_INTERFACE=public
export OS_APPLICATION_CREDENTIAL_ID=your_id_here
export OS_APPLICATION_CREDENTIAL_SECRET=your_secret_here

# Run the example
python examples/app_cred_example.py
```

There's also a convenience script to set these variables:
```bash
source examples/set_app_cred_env.sh
```

## Configuration Files

Both `config.yaml` and `minimal-config.yaml` support application credentials. When using application credentials, the configuration should contain the following fields:

```yaml
# For application credentials authentication:
auth_url: "${OS_AUTH_URL}"
auth_type: "${OS_AUTH_TYPE}"
region: "${OS_REGION_NAME}"
project_name: "${OS_TENANT_NAME}"
application_credential_id: "${OS_APPLICATION_CREDENTIAL_ID}"
application_credential_secret: "${OS_APPLICATION_CREDENTIAL_SECRET}"
```

For traditional username/password authentication, use:
```yaml
# For traditional authentication:
auth_url: "https://auth.cloud.ovh.net/v3"
username: "${OS_USERNAME}"
password: "${OS_PASSWORD}"
tenant_name: "${OS_TENANT_NAME}"
region: "GRA7"
project_name: "my-project"
```

## Configuration Examples

### Minimal Configuration

`minimal-config.yaml` - A minimal configuration example showing the essential fields needed for deployment.

### Complete Configuration

`config.yaml` - A comprehensive example showing all supported resource types and their configuration options.

### JSON Configuration

`config.json` - The same configuration as `config.yaml` but in JSON format.

## Resource Examples

Each example file demonstrates how to work with a specific resource type:

- `compute_example.py` - Compute instances
- `network_example.py` - Networks and subnets  
- `security_group_example.py` - Security groups
- `volume_example.py` - Storage volumes

## Running Examples

To run any example:

```bash
python examples/<example-name>.py
```

Note: Examples require proper authentication environment variables to be set. For application credentials, see the authentication examples above.