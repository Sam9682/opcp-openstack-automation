#!/usr/bin/env python3
"""
Example deployment script using the OpenStack SDK deployment engine.

This script demonstrates a complete deployment workflow:
1. Load credentials from environment
2. Create deployment configuration
3. Deploy infrastructure
4. Handle results
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.models import (
    DeploymentConfig, NetworkSpec, SubnetSpec,
    SecurityGroupSpec, SecurityGroupRule, InstanceSpec, VolumeSpec
)
from openstack_sdk import DeploymentEngine, AuthenticationManager
from utils.logger import setup_logging, get_logger


def create_example_config(credentials) -> DeploymentConfig:
    """
    Create an example deployment configuration.
    
    Args:
        credentials: Authentication credentials
        
    Returns:
        DeploymentConfig object
    """
    return DeploymentConfig(
        auth_url=credentials.auth_url,
        username=credentials.username,
        password=credentials.password,
        tenant_name=credentials.tenant_name,
        region=credentials.region,
        project_name=credentials.tenant_name,
        
        # Define network infrastructure
        networks=[
            NetworkSpec(
                name="example-network",
                admin_state_up=True,
                external=False,
                subnets=[
                    SubnetSpec(
                        name="example-subnet",
                        cidr="192.168.50.0/24",
                        ip_version=4,
                        enable_dhcp=True,
                        dns_nameservers=["8.8.8.8", "8.8.4.4"]
                    )
                ]
            )
        ],
        
        # Define security groups
        security_groups=[
            SecurityGroupSpec(
                name="example-web-sg",
                description="Security group for web servers",
                rules=[
                    # SSH access
                    SecurityGroupRule(
                        direction="ingress",
                        protocol="tcp",
                        port_range_min=22,
                        port_range_max=22,
                        remote_ip_prefix="0.0.0.0/0",
                        ethertype="IPv4"
                    ),
                    # HTTP access
                    SecurityGroupRule(
                        direction="ingress",
                        protocol="tcp",
                        port_range_min=80,
                        port_range_max=80,
                        remote_ip_prefix="0.0.0.0/0",
                        ethertype="IPv4"
                    ),
                    # HTTPS access
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
        ],
        
        # Define compute instances
        instances=[
            InstanceSpec(
                name="example-web-1",
                flavor="s1-2",  # Adjust based on your OVH region
                image="Ubuntu 22.04",  # Adjust based on available images
                key_name="my-ssh-key",  # Replace with your SSH key name
                network_ids=[],  # Will be populated after network creation
                security_groups=["example-web-sg"],
                metadata={
                    "environment": "example",
                    "role": "web-server",
                    "project": "ovh-deployment-demo"
                }
            )
        ],
        
        # Define volumes
        volumes=[
            VolumeSpec(
                name="example-data-volume",
                size=20,  # 20 GB
                volume_type="classic",
                bootable=False,
                attach_to="example-web-1"
            )
        ]
    )


def main():
    """Main function."""
    # Set up logging
    logger = setup_logging(log_level="INFO")
    
    logger.info("=" * 70)
    logger.info("OVH OpenStack Deployment Example")
    logger.info("=" * 70)
    
    # Step 1: Load credentials from environment
    logger.info("\n[Step 1] Loading credentials from environment variables")
    auth_mgr = AuthenticationManager(logger=logger)
    
    try:
        credentials = auth_mgr.load_credentials_from_env()
        logger.info("✓ Credentials loaded successfully")
        logger.info(f"  - Auth URL: {credentials.auth_url}")
        logger.info(f"  - Region: {credentials.region}")
        logger.info(f"  - Tenant: {credentials.tenant_name}")
    except Exception as e:
        logger.error(f"✗ Failed to load credentials: {e}")
        logger.info("\nPlease set the following environment variables:")
        logger.info("  OS_AUTH_URL       - OpenStack authentication URL")
        logger.info("  OS_USERNAME       - Your username")
        logger.info("  OS_PASSWORD       - Your password")
        logger.info("  OS_TENANT_NAME    - Your tenant/project name")
        logger.info("  OS_REGION_NAME    - OVH region (e.g., GRA7, SBG5, BHS5)")
        logger.info("\nAlternatively, use application credentials:")
        logger.info("  OS_APPLICATION_CREDENTIAL_ID")
        logger.info("  OS_APPLICATION_CREDENTIAL_SECRET")
        return 1
    
    # Step 2: Create deployment configuration
    logger.info("\n[Step 2] Creating deployment configuration")
    config = create_example_config(credentials)
    
    logger.info("✓ Configuration created:")
    logger.info(f"  - Networks: {len(config.networks)}")
    logger.info(f"  - Security Groups: {len(config.security_groups)}")
    logger.info(f"  - Instances: {len(config.instances)}")
    logger.info(f"  - Volumes: {len(config.volumes)}")
    
    # Step 3: Create deployment engine
    logger.info("\n[Step 3] Initializing deployment engine")
    engine = DeploymentEngine(credentials, logger=logger)
    logger.info("✓ Deployment engine initialized")
    
    # Step 4: Deploy infrastructure
    logger.info("\n[Step 4] Deploying infrastructure")
    logger.info("This may take several minutes...")
    logger.info("-" * 70)
    
    result = engine.deploy_infrastructure(config)
    
    logger.info("-" * 70)
    
    # Step 5: Display results
    logger.info("\n[Step 5] Deployment Results")
    logger.info("=" * 70)
    
    if result.success:
        logger.info("✓ DEPLOYMENT SUCCESSFUL")
        logger.info(f"\nDeployment ID: {result.deployment_id}")
        logger.info(f"Duration: {result.duration_seconds:.2f} seconds")
        logger.info(f"Timestamp: {result.timestamp}")
        
        logger.info("\nCreated Resources:")
        total_resources = 0
        for resource_type, ids in result.created_resources.items():
            if ids:
                logger.info(f"  {resource_type.capitalize()}:")
                for resource_id in ids:
                    logger.info(f"    - {resource_id}")
                total_resources += len(ids)
        
        logger.info(f"\nTotal: {total_resources} resource(s) created")
        
        logger.info("\n" + "=" * 70)
        logger.info("Next Steps:")
        logger.info("  1. Verify resources in OVH control panel")
        logger.info("  2. Connect to instances using SSH")
        logger.info("  3. Configure applications on instances")
        logger.info("\nTo cleanup resources, use:")
        logger.info("  engine.cleanup_resources(result.created_resources)")
        logger.info("=" * 70)
        
        return 0
    
    else:
        logger.error("✗ DEPLOYMENT FAILED")
        logger.error(f"\nDeployment ID: {result.deployment_id}")
        logger.error(f"Duration: {result.duration_seconds:.2f} seconds")
        logger.error(f"Timestamp: {result.timestamp}")
        
        if result.failed_resources:
            logger.error("\nFailed Resources:")
            for failed in result.failed_resources:
                logger.error(f"  Type: {failed.resource_type}")
                logger.error(f"  Name: {failed.resource_name}")
                logger.error(f"  Error: {failed.error_message}")
                logger.error("")
        
        if result.orphaned_resources:
            logger.warning("\nOrphaned Resources (manual cleanup required):")
            for orphaned in result.orphaned_resources:
                logger.warning(f"  - {orphaned}")
        
        logger.error("\n" + "=" * 70)
        logger.error("Troubleshooting:")
        logger.error("  1. Check credentials are correct")
        logger.error("  2. Verify SSH key exists in OVH account")
        logger.error("  3. Ensure flavor and image names are correct for your region")
        logger.error("  4. Check you have sufficient quota")
        logger.error("  5. Review error messages above")
        logger.error("=" * 70)
        
        return 1


if __name__ == "__main__":
    sys.exit(main())
